"""
Knowledge Graph Builder - Stage 3 of the pipeline
Converts extracted entities and relations into structured graph.
Handles deduplication, normalization, and validation.
"""

import json
from collections import defaultdict
from typing import Set

class KnowledgeGraph:
    """
    Knowledge graph structure with deduplication and validation.
    """
    
    def __init__(self):
        self.entities = {}  # entity_name -> {type, frequency, contexts}
        self.relations = []  # list of (subject, relation, object, context)
        self.relation_types = set()
        self.entity_pairs = set()  # for deduplication
        
    def add_entity(self, name: str, entity_type: str = 'UNKNOWN', context: str = ''):
        """
        Add or update entity.
        
        Args:
            name: Entity name
            entity_type: Entity type (TECH, SYSTEM, STANDARD, etc.)
            context: Context where entity appears
        """
        name = self._normalize_entity(name)
        
        if name in self.entities:
            self.entities[name]['frequency'] += 1
            if context and context not in self.entities[name]['contexts']:
                self.entities[name]['contexts'].append(context)
        else:
            self.entities[name] = {
                'type': entity_type,
                'frequency': 1,
                'contexts': [context] if context else []
            }
    
    def add_relation(self, subject: str, relation: str, obj: str, context: str = ''):
        """
        Add relation triple with deduplication.
        
        Args:
            subject: Subject entity
            relation: Relation type
            obj: Object entity
            context: Context sentence
        """
        subject = self._normalize_entity(subject)
        obj = self._normalize_entity(obj)
        relation = self._normalize_relation(relation)
        
        # Validate
        if not subject or not obj or not relation:
            return
        
        if subject == obj:  # Self-loop
            return
        
        # Deduplicate
        pair_key = (subject, relation, obj)
        if pair_key in self.entity_pairs:
            return
        
        self.entity_pairs.add(pair_key)
        
        # Add entities if not exist
        self.add_entity(subject, context=context)
        self.add_entity(obj, context=context)
        
        # Add relation
        self.relations.append({
            'subject': subject,
            'relation': relation,
            'object': obj,
            'context': context
        })
        self.relation_types.add(relation)
    
    def _normalize_entity(self, name: str) -> str:
        """
        Normalize entity name.
        """
        if not name:
            return ''
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['该', '本', '所述', '上述']
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):]
        
        return name.strip()
    
    def _normalize_relation(self, relation: str) -> str:
        """
        Normalize relation name.
        """
        if not relation:
            return ''
        
        # Remove extra whitespace
        relation = ' '.join(relation.split())
        
        # Standardize common variations
        relation_mapping = {
            '包含': '包括',
            '包括有': '包括',
            '由...组成': '包括',
            '应用于': '用于',
            '适用于': '用于',
            '依据': '基于',
            '遵循': '基于',
            '符合': '基于',
        }
        
        return relation_mapping.get(relation, relation)
    
    def merge_similar_entities(self, similarity_threshold: float = 0.8):
        """
        Merge entities with similar names (fuzzy matching).
        This is a simple implementation - can be enhanced with embeddings.
        """
        # Group by normalized prefix
        groups = defaultdict(list)
        
        for entity_name in list(self.entities.keys()):
            # Simple grouping by first 3 characters
            if len(entity_name) >= 3:
                prefix = entity_name[:3]
                groups[prefix].append(entity_name)
        
        # Merge groups with exact matches on abbreviations
        for group in groups.values():
            if len(group) <= 1:
                continue
            
            # Sort by frequency (keep most common as canonical)
            group.sort(key=lambda x: self.entities[x]['frequency'], reverse=True)
            canonical = group[0]
            
            for variant in group[1:]:
                # Simple check: if variant is substring or very similar
                if variant in canonical or canonical in variant:
                    # Merge
                    self.entities[canonical]['frequency'] += self.entities[variant]['frequency']
                    self.entities[canonical]['contexts'].extend(self.entities[variant]['contexts'])
                    
                    # Update relations
                    for rel in self.relations:
                        if rel['subject'] == variant:
                            rel['subject'] = canonical
                        if rel['object'] == variant:
                            rel['object'] = canonical
                    
                    # Remove variant
                    del self.entities[variant]
    
    def get_statistics(self) -> dict:
        """
        Get graph statistics.
        """
        return {
            'num_entities': len(self.entities),
            'num_relations': len(self.relations),
            'num_relation_types': len(self.relation_types),
            'relation_types': sorted(list(self.relation_types)),
            'top_entities': self._get_top_entities(10)
        }
    
    def _get_top_entities(self, n: int = 10) -> list:
        """
        Get top N most frequent entities.
        """
        sorted_entities = sorted(
            self.entities.items(),
            key=lambda x: x[1]['frequency'],
            reverse=True
        )
        return [
            {
                'name': name,
                'type': data['type'],
                'frequency': data['frequency']
            }
            for name, data in sorted_entities[:n]
        ]
    
    def to_dict(self) -> dict:
        """
        Convert graph to dictionary format.
        """
        return {
            'entities': [
                {
                    'name': name,
                    **data
                }
                for name, data in self.entities.items()
            ],
            'relations': self.relations,
            'statistics': self.get_statistics()
        }
    
    def save(self, output_path: str):
        """
        Save knowledge graph to JSON file.
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        print(f"✓ Knowledge graph saved to {output_path}")
        print(f"  Entities: {len(self.entities)}")
        print(f"  Relations: {len(self.relations)}")
        print(f"  Relation types: {len(self.relation_types)}")

def build_graph_from_triples(triples: list[dict], entities: dict = None) -> KnowledgeGraph:
    """
    Build knowledge graph from extracted triples.
    
    Args:
        triples: List of {subject, relation, object, context?} dicts
        entities: Optional dict of entity_name -> type mappings
        
    Returns:
        KnowledgeGraph instance
    """
    kg = KnowledgeGraph()
    
    # Add entities first (if provided)
    if entities:
        for name, entity_type in entities.items():
            kg.add_entity(name, entity_type)
    
    # Add relations
    for triple in triples:
        kg.add_relation(
            subject=triple.get('subject', ''),
            relation=triple.get('relation', ''),
            obj=triple.get('object', ''),
            context=triple.get('context', '')
        )
    
    # Post-processing
    kg.merge_similar_entities()
    
    return kg

if __name__ == '__main__':
    # Test
    print("Testing Graph Builder:")
    print("="*60)
    
    test_triples = [
        {"subject": "CBTC", "relation": "包括", "object": "ZC", "context": "CBTC包括ZC"},
        {"subject": "CBTC", "relation": "包括", "object": "ATS", "context": "CBTC包括ATS"},
        {"subject": "ZC", "relation": "用于", "object": "列车运行控制", "context": "ZC用于列车运行控制"},
        {"subject": "CBTC", "relation": "包含", "object": "ZC", "context": "CBTC包含ZC"},  # Duplicate (normalized)
    ]
    
    kg = build_graph_from_triples(test_triples)
    
    print("\nGraph Statistics:")
    stats = kg.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Save
    output_path = '/Users/dp/Agent_research/design/AgentTree/output/test_knowledge_graph.json'
    kg.save(output_path)
