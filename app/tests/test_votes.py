import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.models.poll import Poll
from app.models.vote import Vote
from app.models.option import Option


class TestVoteRoutes:
    """Test cases for vote routes."""
    
    def test_cast_vote(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test casting a vote."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option.id)]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["poll_id"] == str(test_poll.id)
        assert data["data"][0]["option_id"] == str(option.id)
    
    def test_cast_vote_with_anonymous_id(self, client: TestClient, db_session: Session, test_poll: Poll, anonymous_user_id: str):
        """Test casting a vote with anonymous ID."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option.id)],
            "anon_id": anonymous_user_id
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["anon_id"] == anonymous_user_id
    
    def test_cast_multiple_votes(self, client: TestClient, db_session: Session, multiple_choice_poll: Poll):
        """Test casting multiple votes on a multiple choice poll."""
        # Get all options
        options = db_session.query(Option).filter(Option.poll_id == multiple_choice_poll.id).all()
        option_ids = [str(option.id) for option in options[:2]]  # Vote for first 2 options
        
        vote_data = {
            "poll_id": str(multiple_choice_poll.id),
            "option_ids": option_ids
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert all(vote["poll_id"] == str(multiple_choice_poll.id) for vote in data["data"])
    
    def test_cast_vote_on_expired_poll(self, client: TestClient, db_session: Session, expired_poll: Poll):
        """Test casting a vote on an expired poll."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == expired_poll.id).first()
        
        vote_data = {
            "poll_id": str(expired_poll.id),
            "option_ids": [str(option.id)]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "expired" in data["message"].lower()
    
    def test_cast_vote_on_inactive_poll(self, client: TestClient, db_session: Session, inactive_poll: Poll):
        """Test casting a vote on an inactive poll."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == inactive_poll.id).first()
        
        vote_data = {
            "poll_id": str(inactive_poll.id),
            "option_ids": [str(option.id)]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "inactive" in data["message"].lower()
    
    def test_cast_multiple_votes_on_single_choice_poll(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test casting multiple votes on a single choice poll."""
        # Get first two options
        options = db_session.query(Option).filter(Option.poll_id == test_poll.id).all()
        option_ids = [str(option.id) for option in options[:2]]
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": option_ids
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "multiple" in data["message"].lower()
    
    def test_cast_vote_with_invalid_option(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test casting a vote with an invalid option ID."""
        fake_option_id = "00000000-0000-0000-0000-000000000000"
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [fake_option_id]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 400
        
        data = response.json()
        assert data["success"] is False
        assert "invalid" in data["message"].lower()
    
    def test_cast_vote_with_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test casting a vote on a non-existent poll."""
        fake_poll_id = "00000000-0000-0000-0000-000000000000"
        fake_option_id = "00000000-0000-0000-0000-000000000000"
        
        vote_data = {
            "poll_id": fake_poll_id,
            "option_ids": [fake_option_id]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_duplicate_vote(self, client: TestClient, db_session: Session, test_poll: Poll, test_vote: Vote):
        """Test casting a duplicate vote."""
        # Get the option that was already voted on
        option_id = test_vote.option_id
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option_id)]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 409
        
        data = response.json()
        assert data["success"] is False
        assert "already voted" in data["message"].lower()
    
    def test_get_poll_votes(self, client: TestClient, db_session: Session, test_poll: Poll, test_vote: Vote):
        """Test getting votes for a specific poll."""
        response = client.get(f"/votes/poll/{test_poll.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Check if our test vote is in the results
        vote_ids = [vote["id"] for vote in data["data"]]
        assert str(test_vote.id) in vote_ids
    
    def test_get_poll_vote_stats(self, client: TestClient, db_session: Session, test_poll: Poll, test_vote: Vote):
        """Test getting vote statistics for a poll."""
        response = client.get(f"/votes/poll/{test_poll.id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_votes" in data["data"]
        assert "unique_voters" in data["data"]
        assert "votes_by_option" in data["data"]
    
    def test_get_user_votes(self, client: TestClient, db_session: Session, test_user, test_vote: Vote):
        """Test getting votes by a specific user."""
        response = client.get(f"/votes/user/{test_user.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Check if our test vote is in the results
        vote_ids = [vote["id"] for vote in data["data"]]
        assert str(test_vote.id) in vote_ids
    
    def test_get_anonymous_votes(self, client: TestClient, db_session: Session, anonymous_user_id: str):
        """Test getting votes by an anonymous user."""
        response = client.get(f"/votes/anonymous/{anonymous_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_vote_by_id(self, client: TestClient, db_session: Session, test_vote: Vote):
        """Test getting a specific vote by ID."""
        response = client.get(f"/votes/{test_vote.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_vote.id)
        assert data["data"]["poll_id"] == str(test_vote.poll_id)
        assert data["data"]["option_id"] == str(test_vote.option_id)
    
    def test_get_nonexistent_vote(self, client: TestClient, db_session: Session):
        """Test getting a vote that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/votes/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_delete_vote(self, client: TestClient, db_session: Session, test_vote: Vote):
        """Test deleting a vote."""
        response = client.delete(f"/votes/{test_vote.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()
        
        # Verify vote is deleted
        get_response = client.get(f"/votes/{test_vote.id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_vote(self, client: TestClient, db_session: Session):
        """Test deleting a vote that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/votes/{fake_id}")
        assert response.status_code == 404
    
    def test_vote_pagination(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test vote pagination."""
        # Create multiple votes
        options = db_session.query(Option).filter(Option.poll_id == test_poll.id).all()
        for i in range(5):
            vote_data = {
                "poll_id": str(test_poll.id),
                "option_ids": [str(options[i % len(options)].id)],
                "anon_id": f"anon_{i}"
            }
            client.post("/votes/", json=vote_data)
        
        # Test pagination
        response = client.get(f"/votes/poll/{test_poll.id}?skip=0&limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 3
        assert "page" in data
        assert "per_page" in data
        assert "total" in data
    
    def test_vote_filtering(self, client: TestClient, db_session: Session):
        """Test vote filtering."""
        response = client.get("/votes/?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_vote_with_ip_address(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test casting a vote with IP address."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
        
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option.id)],
            "anon_id": "test_anon",
            "ip_address": "192.168.1.1",
            "user_agent": "Test Browser"
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"][0]["anon_id"] == "test_anon"
    
    def test_vote_validation(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test vote validation."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
        
        # Test with empty option_ids
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": []
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 422
        
        # Test with duplicate option_ids
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option.id), str(option.id)]
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 422
    
    def test_vote_count_updates(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test that vote counts are updated correctly."""
        # Get first option
        option = db_session.query(Option).filter(Option.poll_id == test_poll.id).first()
        initial_count = option.vote_count
        
        # Cast a vote
        vote_data = {
            "poll_id": str(test_poll.id),
            "option_ids": [str(option.id)],
            "anon_id": "test_anon"
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        # Verify vote count increased
        db_session.refresh(option)
        assert option.vote_count == initial_count + 1
        
        # Verify poll total votes increased
        db_session.refresh(test_poll)
        assert test_poll.total_votes > 0
    
    def test_multiple_vote_count_updates(self, client: TestClient, db_session: Session, multiple_choice_poll: Poll):
        """Test that vote counts are updated correctly for multiple votes."""
        # Get all options
        options = db_session.query(Option).filter(Option.poll_id == multiple_choice_poll.id).all()
        initial_counts = [option.vote_count for option in options]
        
        # Cast multiple votes
        option_ids = [str(option.id) for option in options[:2]]
        vote_data = {
            "poll_id": str(multiple_choice_poll.id),
            "option_ids": option_ids,
            "anon_id": "test_anon"
        }
        
        response = client.post("/votes/", json=vote_data)
        assert response.status_code == 201
        
        # Verify vote counts increased
        for i, option in enumerate(options[:2]):
            db_session.refresh(option)
            assert option.vote_count == initial_counts[i] + 1
        
        # Verify poll total votes increased
        db_session.refresh(multiple_choice_poll)
        assert multiple_choice_poll.total_votes >= 2
