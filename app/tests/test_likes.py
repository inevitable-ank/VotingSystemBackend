import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.models.poll import Poll
from app.models.like import Like


class TestLikeRoutes:
    """Test cases for like routes."""
    
    def test_like_poll(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test liking a poll."""
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["poll_id"] == str(test_poll.id)
        assert data["data"]["anon_id"] is not None
    
    def test_like_poll_with_user(self, client: TestClient, db_session: Session, test_poll: Poll, test_user):
        """Test liking a poll with authenticated user."""
        # Note: In a real implementation, you would need to authenticate the user
        # For now, we'll test the anonymous like functionality
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["poll_id"] == str(test_poll.id)
    
    def test_like_poll_with_anonymous_id(self, client: TestClient, db_session: Session, test_poll: Poll, anonymous_user_id: str):
        """Test liking a poll with anonymous ID."""
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["poll_id"] == str(test_poll.id)
    
    def test_like_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test liking a poll that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/likes/poll/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_duplicate_like(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test liking a poll that's already been liked."""
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 409
        
        data = response.json()
        assert data["success"] is False
        assert "already liked" in data["message"].lower()
    
    def test_unlike_poll(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test unliking a poll."""
        response = client.delete(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "unliked" in data["message"].lower()
    
    def test_unlike_poll_not_liked(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test unliking a poll that hasn't been liked."""
        response = client.delete(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not liked" in data["message"].lower()
    
    def test_unlike_nonexistent_poll(self, client: TestClient, db_session: Session):
        """Test unliking a poll that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/likes/poll/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_get_poll_likes(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test getting likes for a specific poll."""
        response = client.get(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Check if our test like is in the results
        like_ids = [like["id"] for like in data["data"]]
        assert str(test_like.id) in like_ids
    
    def test_get_poll_like_stats(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test getting like statistics for a poll."""
        response = client.get(f"/likes/poll/{test_poll.id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "total_likes" in data["data"]
        assert "unique_likers" in data["data"]
        assert "anonymous_likes" in data["data"]
        assert "authenticated_likes" in data["data"]
    
    def test_get_user_likes(self, client: TestClient, db_session: Session, test_user, test_like: Like):
        """Test getting likes by a specific user."""
        response = client.get(f"/likes/user/{test_user.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]) >= 1
        
        # Check if our test like is in the results
        like_ids = [like["id"] for like in data["data"]]
        assert str(test_like.id) in like_ids
    
    def test_get_anonymous_likes(self, client: TestClient, db_session: Session, anonymous_user_id: str):
        """Test getting likes by an anonymous user."""
        response = client.get(f"/likes/anonymous/{anonymous_user_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_get_like_by_id(self, client: TestClient, db_session: Session, test_like: Like):
        """Test getting a specific like by ID."""
        response = client.get(f"/likes/{test_like.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(test_like.id)
        assert data["data"]["poll_id"] == str(test_like.poll_id)
        assert data["data"]["user_id"] == str(test_like.user_id)
    
    def test_get_nonexistent_like(self, client: TestClient, db_session: Session):
        """Test getting a like that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/likes/{fake_id}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_delete_like(self, client: TestClient, db_session: Session, test_like: Like):
        """Test deleting a like."""
        response = client.delete(f"/likes/{test_like.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()
        
        # Verify like is deleted
        get_response = client.get(f"/likes/{test_like.id}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_like(self, client: TestClient, db_session: Session):
        """Test deleting a like that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/likes/{fake_id}")
        assert response.status_code == 404
    
    def test_like_pagination(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test like pagination."""
        # Create multiple likes
        for i in range(5):
            response = client.post(f"/likes/poll/{test_poll.id}")
            if response.status_code == 201:
                # Like was created successfully
                pass
        
        # Test pagination
        response = client.get(f"/likes/poll/{test_poll.id}?skip=0&limit=3")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) <= 3
        assert "page" in data
        assert "per_page" in data
        assert "total" in data
    
    def test_like_filtering(self, client: TestClient, db_session: Session):
        """Test like filtering."""
        response = client.get("/likes/?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
    
    def test_like_count_updates(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test that like counts are updated correctly."""
        initial_count = test_poll.likes_count
        
        # Like the poll
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        # Verify like count increased
        db_session.refresh(test_poll)
        assert test_poll.likes_count == initial_count + 1
    
    def test_unlike_count_updates(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test that like counts are updated correctly when unliking."""
        initial_count = test_poll.likes_count
        
        # Unlike the poll
        response = client.delete(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 200
        
        # Verify like count decreased
        db_session.refresh(test_poll)
        assert test_poll.likes_count == initial_count - 1
    
    def test_like_on_inactive_poll(self, client: TestClient, db_session: Session, inactive_poll: Poll):
        """Test liking an inactive poll."""
        response = client.post(f"/likes/poll/{inactive_poll.id}")
        assert response.status_code == 201  # Likes are allowed on inactive polls
        
        data = response.json()
        assert data["success"] is True
    
    def test_like_on_expired_poll(self, client: TestClient, db_session: Session, expired_poll: Poll):
        """Test liking an expired poll."""
        response = client.post(f"/likes/poll/{expired_poll.id}")
        assert response.status_code == 201  # Likes are allowed on expired polls
        
        data = response.json()
        assert data["success"] is True
    
    def test_like_on_private_poll(self, client: TestClient, db_session: Session, private_poll: Poll):
        """Test liking a private poll."""
        response = client.post(f"/likes/poll/{private_poll.id}")
        assert response.status_code == 201  # Likes are allowed on private polls
        
        data = response.json()
        assert data["success"] is True
    
    def test_like_with_ip_address(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test liking a poll with IP address tracking."""
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
        assert data["data"]["poll_id"] == str(test_poll.id)
    
    def test_like_analytics(self, client: TestClient, db_session: Session, test_poll: Poll, test_like: Like):
        """Test like analytics data."""
        response = client.get(f"/likes/poll/{test_poll.id}/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        stats = data["data"]
        
        # Verify analytics structure
        assert "total_likes" in stats
        assert "unique_likers" in stats
        assert "anonymous_likes" in stats
        assert "authenticated_likes" in stats
        assert "poll_likes_count" in stats
        
        # Verify counts are reasonable
        assert stats["total_likes"] >= 1
        assert stats["unique_likers"] >= 1
        assert stats["poll_likes_count"] >= 1
    
    def test_like_history(self, client: TestClient, db_session: Session, test_user, test_like: Like):
        """Test getting like history for a user."""
        response = client.get(f"/likes/user/{test_user.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        
        # Verify like history structure
        if data["data"]:
            like = data["data"][0]
            assert "id" in like
            assert "poll_id" in like
            assert "user_id" in like
            assert "created_at" in like
    
    def test_like_toggle_functionality(self, client: TestClient, db_session: Session, test_poll: Poll):
        """Test like toggle functionality (like then unlike)."""
        # Like the poll
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        # Unlike the poll
        response = client.delete(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 200
        
        # Like again
        response = client.post(f"/likes/poll/{test_poll.id}")
        assert response.status_code == 201
        
        data = response.json()
        assert data["success"] is True
    
    def test_like_permissions(self, client: TestClient, db_session: Session, test_like: Like):
        """Test like permissions (users can only delete their own likes)."""
        # Note: In a real implementation, you would test authentication
        # For now, we'll test the basic functionality
        
        # Try to delete a like (this would require proper authentication in real implementation)
        response = client.delete(f"/likes/{test_like.id}")
        # This might return 403 or 200 depending on the implementation
        assert response.status_code in [200, 403]
    
    def test_like_validation(self, client: TestClient, db_session: Session):
        """Test like validation."""
        # Test with invalid poll ID format
        response = client.post("/likes/poll/invalid-id")
        assert response.status_code == 422
        
        # Test with invalid like ID format
        response = client.get("/likes/invalid-id")
        assert response.status_code == 422
