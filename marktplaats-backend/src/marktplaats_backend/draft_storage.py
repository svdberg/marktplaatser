import os
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Force AWS region to eu-west-1 at the very start
os.environ['AWS_REGION'] = 'eu-west-1'

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('marktplaats-draft-listings')


class DraftListing:
    """
    Represents a draft listing that hasn't been published to Marktplaats yet.
    """
    
    def __init__(self, 
                 draft_id: str = None,
                 user_id: str = None,
                 title: str = None,
                 description: str = None,
                 category_id: int = None,
                 category_name: str = None,
                 attributes: List[Dict] = None,
                 price_model: Dict = None,
                 postcode: str = None,
                 images: List[str] = None,
                 ai_generated: bool = False,
                 status: str = "draft",
                 created_at: str = None,
                 updated_at: str = None,
                 **kwargs):
        
        self.draft_id = draft_id or str(uuid.uuid4())
        self.user_id = user_id
        self.title = title
        self.description = description
        self.category_id = category_id
        self.category_name = category_name
        self.attributes = attributes or []
        self.price_model = price_model or {}
        self.postcode = postcode
        self.images = images or []
        self.ai_generated = ai_generated
        self.status = status  # draft, editing, ready_to_publish
        
        # Timestamps
        now = datetime.utcnow().isoformat()
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        
        # Handle any additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the draft listing to a dictionary for DynamoDB storage."""
        def convert_decimals(obj):
            """Recursively convert Decimal objects to int/float for JSON serialization."""
            if isinstance(obj, Decimal):
                if obj % 1 == 0:
                    return int(obj)
                else:
                    return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(v) for v in obj]
            return obj
        
        data = {
            'draftId': self.draft_id,
            'userId': self.user_id,
            'title': self.title,
            'description': self.description,
            'categoryId': self.category_id,
            'categoryName': self.category_name,
            'attributes': self.attributes,
            'priceModel': self.price_model,
            'postcode': self.postcode,
            'images': self.images,
            'aiGenerated': self.ai_generated,
            'status': self.status,
            'createdAt': self.created_at,
            'updatedAt': self.updated_at
        }
        
        # Convert any Decimal objects to JSON-serializable types
        return convert_decimals(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DraftListing':
        """Create a DraftListing instance from a dictionary."""
        return cls(
            draft_id=data.get('draftId'),
            user_id=data.get('userId'),
            title=data.get('title'),
            description=data.get('description'),
            category_id=data.get('categoryId'),
            category_name=data.get('categoryName'),
            attributes=data.get('attributes', []),
            price_model=data.get('priceModel', {}),
            postcode=data.get('postcode'),
            images=data.get('images', []),
            ai_generated=data.get('aiGenerated', False),
            status=data.get('status', 'draft'),
            created_at=data.get('createdAt'),
            updated_at=data.get('updatedAt')
        )
    
    def update_fields(self, **kwargs) -> None:
        """Update specific fields and set updated_at timestamp."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow().isoformat()


def create_draft(draft_listing: DraftListing) -> DraftListing:
    """
    Create a new draft listing in DynamoDB.
    
    Args:
        draft_listing: DraftListing instance to save
        
    Returns:
        DraftListing: The saved draft listing
        
    Raises:
        ValueError: If required fields are missing
        ClientError: If DynamoDB operation fails
    """
    if not draft_listing.user_id:
        raise ValueError("user_id is required")
    
    if not draft_listing.title:
        raise ValueError("title is required")
    
    try:
        # Ensure updated timestamp
        draft_listing.updated_at = datetime.utcnow().isoformat()
        
        # Save to DynamoDB
        table.put_item(Item=draft_listing.to_dict())
        
        print(f"Created draft listing {draft_listing.draft_id} for user {draft_listing.user_id}")
        return draft_listing
        
    except ClientError as e:
        print(f"Error creating draft listing: {str(e)}")
        raise


def get_draft(draft_id: str, user_id: str) -> Optional[DraftListing]:
    """
    Retrieve a specific draft listing by ID and user ID.
    
    Args:
        draft_id: The draft listing ID
        user_id: The user ID (for ownership verification)
        
    Returns:
        DraftListing: The draft listing if found and owned by user
        None: If not found or not owned by user
        
    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        response = table.get_item(Key={'draftId': draft_id})
        
        if 'Item' not in response:
            return None
        
        draft_data = response['Item']
        
        # Verify ownership
        if draft_data.get('userId') != user_id:
            print(f"Draft {draft_id} not owned by user {user_id}")
            return None
        
        return DraftListing.from_dict(draft_data)
        
    except ClientError as e:
        print(f"Error retrieving draft listing {draft_id}: {str(e)}")
        raise


def list_user_drafts(user_id: str, limit: int = 50, last_evaluated_key: str = None) -> Dict[str, Any]:
    """
    List all draft listings for a specific user.
    
    Args:
        user_id: The user ID
        limit: Maximum number of drafts to return (default 50)
        last_evaluated_key: For pagination (optional)
        
    Returns:
        Dict containing:
        - drafts: List of DraftListing objects
        - last_evaluated_key: For pagination (if more items exist)
        
    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        # Import boto3 Key for condition expressions
        from boto3.dynamodb.conditions import Key
        
        query_params = {
            'IndexName': 'UserIdIndex',
            'KeyConditionExpression': Key('userId').eq(user_id),
            'ScanIndexForward': False,  # Sort by createdAt descending (newest first)
            'Limit': limit
        }
        
        if last_evaluated_key:
            query_params['ExclusiveStartKey'] = json.loads(last_evaluated_key)
        
        response = table.query(**query_params)
        
        drafts = [DraftListing.from_dict(item) for item in response.get('Items', [])]
        
        result = {'drafts': drafts}
        
        if 'LastEvaluatedKey' in response:
            result['last_evaluated_key'] = json.dumps(response['LastEvaluatedKey'])
        
        print(f"Retrieved {len(drafts)} drafts for user {user_id}")
        return result
        
    except ClientError as e:
        print(f"Error listing drafts for user {user_id}: {str(e)}")
        raise


def update_draft(draft_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[DraftListing]:
    """
    Update a draft listing with new field values.
    
    Args:
        draft_id: The draft listing ID
        user_id: The user ID (for ownership verification)
        updates: Dictionary of fields to update
        
    Returns:
        DraftListing: Updated draft listing
        None: If draft not found or not owned by user
        
    Raises:
        ValueError: If trying to update protected fields
        ClientError: If DynamoDB operation fails
    """
    # Protected fields that cannot be updated directly
    protected_fields = {'draftId', 'userId', 'createdAt'}
    
    if any(field in protected_fields for field in updates.keys()):
        raise ValueError(f"Cannot update protected fields: {protected_fields}")
    
    # First, get the existing draft to verify ownership
    existing_draft = get_draft(draft_id, user_id)
    if not existing_draft:
        return None
    
    try:
        # Build update expression with reserved keyword handling
        update_expression = "SET updatedAt = :updated_at"
        expression_values = {':updated_at': datetime.utcnow().isoformat()}
        expression_names = {}
        
        # Reserved keywords in DynamoDB that need special handling
        reserved_keywords = {'status', 'timestamp', 'date', 'time', 'name', 'location', 'data', 'size'}
        
        for field, value in updates.items():
            attr_value_name = f":{field}"
            
            if field.lower() in reserved_keywords:
                # Use expression attribute names for reserved keywords
                attr_name = f"#{field}"
                expression_names[attr_name] = field
                update_expression += f", {attr_name} = {attr_value_name}"
            else:
                update_expression += f", {field} = {attr_value_name}"
            
            expression_values[attr_value_name] = value
        
        # Prepare update parameters
        update_params = {
            'Key': {'draftId': draft_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        # Add expression attribute names if we have any
        if expression_names:
            update_params['ExpressionAttributeNames'] = expression_names
        
        # Perform the update
        response = table.update_item(**update_params)
        
        updated_draft = DraftListing.from_dict(response['Attributes'])
        print(f"Updated draft {draft_id} for user {user_id}")
        
        return updated_draft
        
    except ClientError as e:
        print(f"Error updating draft {draft_id}: {str(e)}")
        raise


def delete_draft(draft_id: str, user_id: str) -> bool:
    """
    Delete a draft listing.
    
    Args:
        draft_id: The draft listing ID
        user_id: The user ID (for ownership verification)
        
    Returns:
        bool: True if deleted successfully, False if not found or not owned
        
    Raises:
        ClientError: If DynamoDB operation fails
    """
    # First verify ownership
    existing_draft = get_draft(draft_id, user_id)
    if not existing_draft:
        return False
    
    try:
        table.delete_item(Key={'draftId': draft_id})
        print(f"Deleted draft {draft_id} for user {user_id}")
        return True
        
    except ClientError as e:
        print(f"Error deleting draft {draft_id}: {str(e)}")
        raise


def create_draft_from_ai_generation(user_id: str, ai_result: Dict[str, Any], 
                                  image_urls: List[str] = None, 
                                  postcode: str = None) -> DraftListing:
    """
    Create a draft listing from AI generation results.
    
    Args:
        user_id: The user ID
        ai_result: Dictionary containing AI-generated listing data
        image_urls: List of S3 image URLs
        postcode: User's postcode for the listing
        
    Returns:
        DraftListing: The created draft listing
        
    Raises:
        ValueError: If required AI result fields are missing
        ClientError: If DynamoDB operation fails
    """
    required_fields = ['title', 'description', 'categoryId']
    missing_fields = [field for field in required_fields if not ai_result.get(field)]
    
    if missing_fields:
        raise ValueError(f"AI result missing required fields: {missing_fields}")
    
    # Create draft from AI results
    draft = DraftListing(
        user_id=user_id,
        title=ai_result.get('title'),
        description=ai_result.get('description'),
        category_id=ai_result.get('categoryId'),
        category_name=ai_result.get('categoryName'),
        attributes=ai_result.get('attributes', []),
        price_model=ai_result.get('priceModel', {}),
        postcode=postcode,
        images=image_urls or [],
        ai_generated=True,
        status='draft'
    )
    
    return create_draft(draft)


def get_draft_count_by_user(user_id: str) -> int:
    """
    Get the total number of draft listings for a user.
    
    Args:
        user_id: The user ID
        
    Returns:
        int: Number of drafts
        
    Raises:
        ClientError: If DynamoDB operation fails
    """
    try:
        from boto3.dynamodb.conditions import Key
        
        response = table.query(
            IndexName='UserIdIndex',
            KeyConditionExpression=Key('userId').eq(user_id),
            Select='COUNT'
        )
        
        return response.get('Count', 0)
        
    except ClientError as e:
        print(f"Error counting drafts for user {user_id}: {str(e)}")
        raise


def validate_draft_for_publishing(draft: DraftListing) -> List[str]:
    """
    Validate that a draft has all required fields for publishing to Marktplaats.
    
    Args:
        draft: The DraftListing to validate
        
    Returns:
        List[str]: List of validation errors (empty if valid)
    """
    errors = []
    
    if not draft.title or len(draft.title.strip()) == 0:
        errors.append("Title is required")
    elif len(draft.title) > 60:
        errors.append("Title must be 60 characters or less")
    
    if not draft.description or len(draft.description.strip()) == 0:
        errors.append("Description is required")
    
    if not draft.category_id:
        errors.append("Category is required")
    
    if not draft.postcode or len(draft.postcode.replace(' ', '')) != 6:
        errors.append("Valid postcode is required (6 characters)")
    
    if not draft.price_model or not draft.price_model.get('askingPrice'):
        errors.append("Price is required")
    elif draft.price_model.get('askingPrice', 0) <= 0:
        errors.append("Price must be greater than 0")
    
    if not draft.images or len(draft.images) == 0:
        errors.append("At least one image is required")
    
    return errors