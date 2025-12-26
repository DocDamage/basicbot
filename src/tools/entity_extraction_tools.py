"""Entity extraction tools for books - characters, locations, and key entities"""

import logging
import re
from typing import Dict, List, Optional, Any, Set
from collections import Counter, defaultdict

logger = logging.getLogger('entity_extraction_tools')

# Try to import spaCy for NER
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_LOADED = True
    except OSError:
        logger.warning("spaCy model 'en_core_web_sm' not found. Install with: python -m spacy download en_core_web_sm")
        SPACY_LOADED = False
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    SPACY_LOADED = False
    nlp = None


def extract_entities(content: str, use_spacy: bool = True) -> Dict[str, List[str]]:
    """
    Extract entities from book content using NER and pattern matching
    
    Args:
        content: Book content text
        use_spacy: Whether to use spaCy NER (if available)
        
    Returns:
        Dictionary with 'characters', 'locations', and 'entities' lists
    """
    result = {
        'characters': [],
        'locations': [],
        'entities': []
    }
    
    if not content:
        return result
    
    # Use spaCy if available
    if use_spacy and SPACY_LOADED and nlp:
        try:
            doc = nlp(content[:1000000])  # Limit to 1M chars for performance
            
            # Extract named entities
            persons = set()
            locations = set()
            organizations = set()
            misc = set()
            
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    persons.add(ent.text.strip())
                elif ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity, Location
                    locations.add(ent.text.strip())
                elif ent.label_ == "ORG":
                    organizations.add(ent.text.strip())
                elif ent.label_ == "MISC":
                    misc.add(ent.text.strip())
            
            result['characters'] = list(persons)
            result['locations'] = list(locations)
            result['entities'] = list(organizations | misc)
            
        except Exception as e:
            logger.warning(f"Error using spaCy NER: {e}, falling back to pattern matching")
            use_spacy = False
    
    # Fallback to pattern matching if spaCy not available or failed
    if not use_spacy or not SPACY_LOADED:
        result = extract_entities_pattern_matching(content)
    
    # Post-process to filter and clean
    result['characters'] = _filter_characters(result['characters'])
    result['locations'] = _filter_locations(result['locations'])
    result['entities'] = _filter_entities(result['entities'])
    
    return result


def extract_entities_pattern_matching(content: str) -> Dict[str, List[str]]:
    """
    Extract entities using pattern matching (fallback method)
    
    Args:
        content: Book content text
        
    Returns:
        Dictionary with extracted entities
    """
    characters = set()
    locations = set()
    entities = set()
    
    lines = content.split('\n')
    
    # Pattern for character names (capitalized words, often at start of sentences)
    # Look for patterns like "John said", "Mary thought", etc.
    character_patterns = [
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:said|thought|replied|asked|whispered|shouted|exclaimed|murmured|laughed|cried|sighed|nodded|shook|smiled|frowned|grinned|gasped|stared|looked|glanced|watched|listened|heard|felt|knew|remembered|forgot|wondered|realized|noticed|decided|tried|began|started|stopped|continued|went|came|walked|ran|stood|sat|lay|fell|rose|turned|opened|closed|picked|put|took|gave|got|made|did|had|was|were)',
        r'"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"',  # Names in quotes
        r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',  # Two capitalized words (likely names)
    ]
    
    # Pattern for locations (often capitalized, may include common location words)
    location_patterns = [
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Street|Avenue|Road|Lane|Boulevard|City|Town|Village|Castle|Palace|Tower|Hall|Manor|House|Building|Park|Forest|River|Lake|Mountain|Hill|Valley|Island|Kingdom|Empire|Realm|Land|Country|Nation|State|Province|Region)',
        r'\b(the|a|an)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # "the Castle", "a Forest"
    ]
    
    for line in lines:
        # Extract potential character names
        for pattern in character_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                name = match.strip()
                if len(name) > 1 and len(name.split()) <= 4:  # Reasonable name length
                    characters.add(name)
        
        # Extract potential locations
        for pattern in location_patterns:
            matches = re.findall(pattern, line)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                location = match.strip()
                if len(location) > 2:
                    locations.add(location)
    
    return {
        'characters': list(characters),
        'locations': list(locations),
        'entities': list(entities)
    }


def _filter_characters(characters: List[str]) -> List[str]:
    """
    Filter and clean character names
    
    Args:
        characters: List of potential character names
        
    Returns:
        Filtered list of character names
    """
    filtered = []
    seen = set()
    
    # Common words to exclude
    exclude_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'if', 'then', 'else',
        'he', 'she', 'it', 'they', 'we', 'you', 'i', 'me', 'him', 'her', 'us', 'them',
        'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom', 'whose',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
        'can', 'cannot', 'must', 'shall', 'ought', 'dare', 'need',
        'said', 'says', 'say', 'told', 'tell', 'tells', 'asked', 'ask', 'asks'
    }
    
    for char in characters:
        char_clean = char.strip()
        
        # Skip if too short or too long
        if len(char_clean) < 2 or len(char_clean) > 50:
            continue
        
        # Skip if all lowercase (likely not a name)
        if char_clean.islower():
            continue
        
        # Skip if contains numbers
        if re.search(r'\d', char_clean):
            continue
        
        # Skip common words
        words = char_clean.split()
        if any(word.lower() in exclude_words for word in words):
            continue
        
        # Skip if already seen (case-insensitive)
        char_lower = char_clean.lower()
        if char_lower not in seen:
            seen.add(char_lower)
            filtered.append(char_clean)
    
    # Sort and return
    return sorted(filtered, key=lambda x: (len(x.split()), x))


def _filter_locations(locations: List[str]) -> List[str]:
    """
    Filter and clean location names
    
    Args:
        locations: List of potential location names
        
    Returns:
        Filtered list of location names
    """
    filtered = []
    seen = set()
    
    for loc in locations:
        loc_clean = loc.strip()
        
        # Skip if too short or too long
        if len(loc_clean) < 2 or len(loc_clean) > 100:
            continue
        
        # Skip if all lowercase
        if loc_clean.islower():
            continue
        
        # Skip if contains only common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for'}
        words = loc_clean.split()
        if len(words) == 1 and words[0].lower() in common_words:
            continue
        
        # Skip if already seen (case-insensitive)
        loc_lower = loc_clean.lower()
        if loc_lower not in seen:
            seen.add(loc_lower)
            filtered.append(loc_clean)
    
    return sorted(filtered, key=lambda x: (len(x.split()), x))


def _filter_entities(entities: List[str]) -> List[str]:
    """
    Filter and clean entity names
    
    Args:
        entities: List of potential entity names
        
    Returns:
        Filtered list of entity names
    """
    filtered = []
    seen = set()
    
    for entity in entities:
        entity_clean = entity.strip()
        
        # Skip if too short or too long
        if len(entity_clean) < 2 or len(entity_clean) > 100:
            continue
        
        # Skip if all lowercase
        if entity_clean.islower():
            continue
        
        # Skip if already seen (case-insensitive)
        entity_lower = entity_clean.lower()
        if entity_lower not in seen:
            seen.add(entity_lower)
            filtered.append(entity_clean)
    
    return sorted(filtered, key=lambda x: (len(x.split()), x))


def build_entity_index(books_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build entity index for cross-referencing across books
    
    Args:
        books_data: List of book data dictionaries with entities
        
    Returns:
        Entity index dictionary
    """
    index = {
        'characters': defaultdict(list),  # character_name -> [book_ids]
        'locations': defaultdict(list),  # location_name -> [book_ids]
        'entities': defaultdict(list),   # entity_name -> [book_ids]
        'character_mentions': defaultdict(int),  # character_name -> mention_count
        'location_mentions': defaultdict(int),   # location_name -> mention_count
    }
    
    for book in books_data:
        book_id = book.get('metadata', {}).get('book_id') or book.get('book_id', '')
        if not book_id:
            continue
        
        # Index characters
        characters = book.get('characters', [])
        for char in characters:
            index['characters'][char].append(book_id)
            index['character_mentions'][char] += 1
        
        # Index locations
        locations = book.get('locations', [])
        for loc in locations:
            index['locations'][loc].append(book_id)
            index['location_mentions'][loc] += 1
        
        # Index entities
        entities = book.get('entities', [])
        for entity in entities:
            index['entities'][entity].append(book_id)
    
    # Convert defaultdicts to regular dicts for JSON serialization
    return {
        'characters': dict(index['characters']),
        'locations': dict(index['locations']),
        'entities': dict(index['entities']),
        'character_mentions': dict(index['character_mentions']),
        'location_mentions': dict(index['location_mentions']),
        'total_books': len(books_data),
        'total_characters': len(index['characters']),
        'total_locations': len(index['locations']),
        'total_entities': len(index['entities'])
    }


def find_related_entities(entity_name: str, entity_type: str, entity_index: Dict[str, Any]) -> List[str]:
    """
    Find books that mention a specific entity
    
    Args:
        entity_name: Name of entity to search for
        entity_type: Type of entity ('characters', 'locations', 'entities')
        entity_index: Entity index dictionary
        
    Returns:
        List of book IDs that mention the entity
    """
    if entity_type not in ['characters', 'locations', 'entities']:
        return []
    
    entity_map = entity_index.get(entity_type, {})
    
    # Try exact match first
    if entity_name in entity_map:
        return entity_map[entity_name]
    
    # Try case-insensitive match
    entity_name_lower = entity_name.lower()
    for key, book_ids in entity_map.items():
        if key.lower() == entity_name_lower:
            return book_ids
    
    # Try partial match
    results = []
    for key, book_ids in entity_map.items():
        if entity_name_lower in key.lower() or key.lower() in entity_name_lower:
            results.extend(book_ids)
    
    return list(set(results))  # Remove duplicates

