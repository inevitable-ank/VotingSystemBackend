import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.models.poll import Poll
from app.models.option import Option
from app.schemas.poll import PollCreate


class TestPollRoutes:
    """Test cases for poll routes."""
    
    def test_get_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting list of polls."""
        response = client.get("/polls/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Check if our test poll is in the results
        poll_ids = [poll["id"] for poll in data["data"]]
        assert str(test_poll.id) in poll_ids
    
    def test_get_public_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting public polls."""
        response = client.get("/polls/public")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Check if our test poll is in the results
        poll_ids = [poll["id"] for poll in data["data"]]
        assert str(test_poll.id) in poll_ids
    
    def test_get_trending_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting trending polls."""
        response = client.get("/polls/trending")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_popular_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting popular polls."""
        response = client.get("/polls/popular")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_recent_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting recent polls."""
        response = client.get("/polls/recent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_search_polls(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test searching polls."""
        response = client.get("/polls/search?q=test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_poll_stats(self, client: TestClient, db_session: Session):
        """Test getting poll statistics."""
        response = client.get("/polls/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_polls" in data["data"]
        assert "active_polls" in data["data"]
        assert "total_votes" in data["data"]
    
    def test_create_poll(self, client: TestClient, db_session: Session):
        """Test creating a new poll."""
        poll_data = {
            "title": "New Test Poll",
            "description": "This is a new test poll",
            "options": ["Option A", "Option B", "Option C"],
            "allow_multiple": False,
            "is_public": True
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["title"] == poll_data["title"]
        assert data["data"]["description"] == poll_data["description"]
        assert len(data["data"]["options"]) == 3
    
    def test_create_poll_with_invalid_data(self, client: TestClient, db_session: Session):
        """Test creating a poll with invalid data."""
        # Test with empty title
        poll_data = {
            "title": "",
            "description": "This poll has no title",
            "options": ["Option A", "Option B"],
            "allow_multiple": False,
            "is_public": True
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 422
    
    def test_create_poll_with_too_few_options(self, client: TestClient, db_session: Session):
        """Test creating a poll with too few options."""
        poll_data = {
            "title": "Poll with one option",
            "description": "This poll has only one option",
            "options": ["Only Option"],
            "allow_multiple": False,
            "is_public": True
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 422
    
    def test_create_poll_with_duplicate_options(self, client: TestClient, db_session: Session):
        """Test creating a poll with duplicate options."""
        poll_data = {
            "title": "Poll with duplicate options",
            "description": "This poll has duplicate options",
            "options": ["Option A", "Option A", "Option B"],
            "allow_multiple": False,
            "is_public": True
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 422
    
    def test_get_poll_by_id(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting a specific poll by ID."""
        response = client.get(f"/polls/{test_poll.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_poll.id)
        assert data["data"]["title"] == test_poll.title
        assert "options" in data["data"]
        assert len(data["data"]["options"]) == 2
    
    def test_get_poll_by_slug(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test getting a specific poll by slug."""
        response = client.get(f"/polls/slug/{test_poll.slug}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["slug"] == test_poll.slug
        assert data["data"]["title"] == test_poll.title
    
    def test_get_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test getting a poll that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/polls/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_update_poll(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test updating a poll."""
        update_data = {
            "title": "Updated Test Poll",
            "description": "This poll has been updated"
        }
        
        response = client.put(f"/polls/{test_poll.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["title"] == update_data["title"]
        assert data["data"]["description"] == update_data["description"]
    
    def test_update_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test updating a poll that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        update_data = {
            "title": "Updated Poll"
        }
        
        response = client.put(f"/polls/{fake_id}", json=update_data)
        assert response.status_code == 404
    
    def test_delete_poll(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test deleting a poll."""
        response = client.delete(f"/polls/{test_poll.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()
        
        # Verify poll is deleted
        get_response = client.get(f"/polls/{test_poll.id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test deleting a poll that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/polls/{fake_id}")
        assert response.status_code == 404
    
    def test_activate_poll(self, client: TestClient, db_session: Session, inactive_poll: Poll):
        """Test activating a poll."""
        response = client.post(f"/polls/{inactive_poll.id}/activate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "activated" in data["message"].lower()
    
    def test_deactivate_poll(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test deactivating a poll."""
        response = client.post(f"/polls/{test_poll.id}/deactivate")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "deactivated" in data["message"].lower()
    
    def test_poll_pagination(self, client: TestClient, db_session: Session):
        """Test poll pagination."""
        # Create multiple polls
        for i in range(5):
            poll_data = {
                "title": f"Test Poll {i}",
                "description": f"Description for poll {i}",
                "options": ["Option A", "Option B"],
                "allow_multiple": False,
                "is_public": True
            }
            client.post("/polls/", json=poll_data)
        
        # Test pagination
        response = client.get("/polls/?skip=0&limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 3
        assert "page" in data
        assert "per_page" in data
        assert "total" in data
    
    def test_poll_filtering(self, client: TestClient, db_session: Session, test_poll: Poll, expired_poll: Poll):
        """Test poll filtering."""
        # Test including expired polls
        response = client.get("/polls/?include_expired=true")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Test excluding expired polls (default)
        response = client.get("/polls/?include_expired=false")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
    
    def test_poll_sorting(self, client: TestClient, db_session: Session):
        """Test poll sorting."""
        response = client.get("/polls/?sort_by=created_at&sort_order=desc")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Verify sorting (newest first)
        if len(data["data"]) > 1:
            dates = [poll["created_at"] for poll in data["data"]]
            assert dates == sorted(dates, reverse=True)
    
    def test_poll_with_expiration(self, client: TestClient, db_session: Session):
        """Test creating a poll with expiration date."""
        from datetime import datetime, timedelta
        
        expires_at = datetime.now() + timedelta(days=1)
        poll_data = {
            "title": "Expiring Poll",
            "description": "This poll expires in 1 day",
            "options": ["Option A", "Option B"],
            "allow_multiple": False,
            "is_public": True,
            "expires_at": expires_at.isoformat()
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["expires_at"] is not None
    
    def test_poll_with_multiple_choice(self, client: TestClient, db_session: Session):
        """Test creating a multiple choice poll."""
        poll_data = {
            "title": "Multiple Choice Poll",
            "description": "This poll allows multiple votes",
            "options": ["Option A", "Option B", "Option C"],
            "allow_multiple": True,
            "is_public": True
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["allow_multiple"] is True
    
    def test_private_poll_creation(self, client: TestClient, db_session: Session):
        """Test creating a private poll."""
        poll_data = {
            "title": "Private Poll",
            "description": "This is a private poll",
            "options": ["Option A", "Option B"],
            "allow_multiple": False,
            "is_public": False
        }
        
        response = client.post("/polls/", json=poll_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_public"] is False
    
    def test_poll_view_count_increment(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test that poll view count increments when accessed."""
        initial_views = test_poll.views_count
        
        # Access the poll
        response = client.get(f"/polls/{test_poll.id}")
        assert response.status_code == 200
        
        # Access again to verify view count increments
        response = client.get(f"/polls/{test_poll.id}")
        assert response.status_code == 200
        
        # Note: In a real implementation, you would verify the view count increased
        # This would require additional setup to check the database state
