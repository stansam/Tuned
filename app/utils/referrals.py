import secrets
import string
import random
from typing import Optional, Set
from flask import current_app
from app.extensions import db
from app.models.user import User


def generate_referral_code(length: int = 8, max_attempts: int = 10) -> str:
    """
    Generate a unique referral code.
    
    Args:
        length (int): Length of the referral code (default: 8)
        max_attempts (int): Maximum attempts to generate unique code (default: 10)
    
    Returns:
        str: Unique referral code
        
    Raises:
        ValueError: If unable to generate unique code after max_attempts
    """
    for attempt in range(max_attempts):
        code = _generate_code(length)
        
        # Check if code is unique
        if not User.query.filter_by(referral_code=code).first():
            current_app.logger.info(f"Generated referral code: {code} (attempt {attempt + 1})")
            return code
    
    # If we couldn't generate a unique code, raise an error
    current_app.logger.error(f"Failed to generate unique referral code after {max_attempts} attempts")
    raise ValueError("Unable to generate unique referral code")


def _generate_code(length: int) -> str:
    """
    Generate a random referral code using multiple strategies.
    
    Args:
        length (int): Length of the code to generate
        
    Returns:
        str: Generated referral code
    """
    # Use different generation strategies for variety
    strategy = random.choice(['alphanumeric', 'consonant_vowel', 'word_based'])
    
    if strategy == 'alphanumeric':
        return _generate_alphanumeric_code(length)
    elif strategy == 'consonant_vowel':
        return _generate_pronounceable_code(length)
    else:
        return _generate_word_based_code(length)


def _generate_alphanumeric_code(length: int) -> str:
    """
    Generate alphanumeric code (excludes confusing characters).
    
    Args:
        length (int): Length of the code
        
    Returns:
        str: Alphanumeric referral code
    """
    # Exclude confusing characters: 0, O, 1, I, l
    safe_chars = 'ABCDEFGHIJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(safe_chars) for _ in range(length))


def _generate_pronounceable_code(length: int) -> str:
    """
    Generate a pronounceable code using consonant-vowel patterns.
    
    Args:
        length (int): Length of the code
        
    Returns:
        str: Pronounceable referral code
    """
    consonants = 'BCDFGHJKLMNPQRSTVWXYZ'
    vowels = 'AEIOU'
    
    code = ''
    for i in range(length):
        if i % 2 == 0:  # Even positions get consonants
            code += secrets.choice(consonants)
        else:  # Odd positions get vowels
            code += secrets.choice(vowels)
    
    return code


def _generate_word_based_code(length: int) -> str:
    """
    Generate code based on word combinations (for longer codes).
    
    Args:
        length (int): Target length of the code
        
    Returns:
        str: Word-based referral code
    """
    adjectives = [
        'BRIGHT', 'SWIFT', 'BOLD', 'WISE', 'KEEN', 'PURE', 'WILD', 'CALM',
        'DEEP', 'WARM', 'COOL', 'FAST', 'STRONG', 'SMART', 'KIND', 'BRAVE'
    ]
    
    nouns = [
        'LION', 'EAGLE', 'WOLF', 'BEAR', 'TIGER', 'HAWK', 'FOX', 'DEER',
        'STORM', 'FIRE', 'WAVE', 'STAR', 'MOON', 'SUN', 'WIND', 'ROCK'
    ]
    
    if length <= 6:
        # For short codes, use numbers
        word = secrets.choice(nouns)
        remaining = length - len(word)
        if remaining > 0:
            numbers = ''.join(secrets.choice('0123456789') for _ in range(remaining))
            return word + numbers
        else:
            return word[:length]
    else:
        # For longer codes, combine adjective + noun
        adj = secrets.choice(adjectives)
        noun = secrets.choice(nouns)
        combined = adj + noun
        
        if len(combined) > length:
            return combined[:length]
        elif len(combined) < length:
            # Add numbers to reach desired length
            remaining = length - len(combined)
            numbers = ''.join(secrets.choice('0123456789') for _ in range(remaining))
            return combined + numbers
        else:
            return combined


def validate_referral_code(code: str) -> bool:
    """
    Validate if a referral code exists and is valid.
    
    Args:
        code (str): Referral code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not code or not isinstance(code, str):
        return False
    
    # Clean the code
    cleaned_code = code.strip().upper()
    
    # Basic format validation
    if not cleaned_code or len(cleaned_code) < 4 or len(cleaned_code) > 20:
        return False
    
    # Check if code exists in database
    user = User.query.filter_by(referral_code=cleaned_code).first()
    return user is not None


def get_user_by_referral_code(code: str) -> Optional[User]:
    """
    Get user by referral code.
    
    Args:
        code (str): Referral code
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    if not validate_referral_code(code):
        return None
    
    cleaned_code = code.strip().upper()
    return User.query.filter_by(referral_code=cleaned_code).first()


def regenerate_referral_code(user_id: int) -> str:
    """
    Regenerate referral code for an existing user.
    
    Args:
        user_id (int): User ID
        
    Returns:
        str: New referral code
        
    Raises:
        ValueError: If user not found or code generation fails
    """
    user = User.query.get(user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    old_code = user.referral_code
    new_code = generate_referral_code()
    
    try:
        user.referral_code = new_code
        db.session.commit()
        
        current_app.logger.info(
            f"Regenerated referral code for user {user.username}: {old_code} -> {new_code}"
        )
        return new_code
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to regenerate referral code for user {user_id}: {str(e)}")
        raise


def get_referral_stats(referrer_id: int) -> dict:
    """
    Get referral statistics for a user.
    
    Args:
        referrer_id (int): ID of the referrer user
        
    Returns:
        dict: Referral statistics
    """
    from app.models.referral import Referral  # Import here to avoid circular imports
    
    try:
        stats = {
            'total_referrals': 0,
            'successful_referrals': 0,
            'pending_referrals': 0,
            'total_rewards': 0
        }
        
        referrals = Referral.query.filter_by(referrer_id=referrer_id).all()
        
        for referral in referrals:
            stats['total_referrals'] += 1
            if referral.is_successful:
                stats['successful_referrals'] += 1
                stats['total_rewards'] += referral.reward_amount or 0
            else:
                stats['pending_referrals'] += 1
        
        return stats
        
    except Exception as e:
        current_app.logger.error(f"Error getting referral stats for user {referrer_id}: {str(e)}")
        return {
            'total_referrals': 0,
            'successful_referrals': 0,
            'pending_referrals': 0,
            'total_rewards': 0
        }


def is_code_format_valid(code: str) -> bool:
    """
    Check if referral code format is valid (without checking database).
    
    Args:
        code (str): Referral code to validate
        
    Returns:
        bool: True if format is valid
    """
    if not code or not isinstance(code, str):
        return False
    
    cleaned_code = code.strip().upper()
    
    # Length check
    if len(cleaned_code) < 4 or len(cleaned_code) > 20:
        return False
    
    # Character check (alphanumeric only)
    if not cleaned_code.isalnum():
        return False
    
    # No purely numeric codes (to avoid confusion with user IDs)
    if cleaned_code.isdigit():
        return False
    
    return True


def bulk_generate_referral_codes(count: int, length: int = 8) -> Set[str]:
    """
    Generate multiple unique referral codes for bulk operations.
    
    Args:
        count (int): Number of codes to generate
        length (int): Length of each code
        
    Returns:
        Set[str]: Set of unique referral codes
        
    Raises:
        ValueError: If unable to generate requested number of codes
    """
    if count <= 0:
        raise ValueError("Count must be positive")
    
    if count > 10000:
        raise ValueError("Cannot generate more than 10,000 codes at once")
    
    codes = set()
    max_attempts = count * 10
    attempts = 0
    
    while len(codes) < count and attempts < max_attempts:
        code = _generate_code(length)
        
        # Check uniqueness in both our set and database
        if code not in codes and not User.query.filter_by(referral_code=code).first():
            codes.add(code)
        
        attempts += 1
    
    if len(codes) < count:
        raise ValueError(f"Could only generate {len(codes)} unique codes out of {count} requested")
    
    current_app.logger.info(f"Bulk generated {len(codes)} referral codes")
    return codes


# Configuration constants
DEFAULT_REFERRAL_CODE_LENGTH = 8
MAX_REFERRAL_CODE_LENGTH = 20
MIN_REFERRAL_CODE_LENGTH = 4