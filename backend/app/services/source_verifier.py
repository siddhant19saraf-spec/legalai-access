import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from app.models.schemas import (
    Jurisdiction, SourceType, Source, LegalCategory
)

logger = logging.getLogger(__name__)


class SourceAuthority(Enum):
    """Authority levels for legal sources"""
    PRIMARY = "primary"      # Official statutes, regulations, case law
    OFFICIAL = "official"    # Government publications, court rules
    SECONDARY = "secondary"  # Legal treatises, law reviews
    TERTIARY = "tertiary"    # Legal aid guides, summaries
    UNVERIFIED = "unverified"


@dataclass
class SourceMetadata:
    """Extended metadata for source verification"""
    source_id: str
    authority: SourceAuthority
    publisher: str
    publication_date: Optional[datetime] = None
    last_verified: Optional[datetime] = None
    verification_method: str = "manual"  # manual, automated, cross_reference
    jurisdiction_specific: bool = True
    applies_to_categories: List[str] = field(default_factory=list)
    superseded_by: Optional[str] = None  # source_id of superseding source
    notes: str = ""
    
    # Quality scores (0.0 to 1.0)
    authority_score: float = 1.0
    currency_score: float = 1.0
    relevance_score: float = 1.0
    
    @property
    def overall_quality(self) -> float:
        return (self.authority_score + self.currency_score + self.relevance_score) / 3
    
    @property
    def is_current(self) -> bool:
        """Check if source is likely still current"""
        if self.last_verified:
            return datetime.utcnow() - self.last_verified < timedelta(days=365)
        if self.publication_date:
            return datetime.utcnow() - self.publication_date < timedelta(days=5*365)
        return False


class SourceVerifier:
    """Verifies and manages legal sources"""
    
    # Known official domains by jurisdiction
    OFFICIAL_DOMAINS = {
        Jurisdiction.US_FEDERAL: {
            "gov", "house.gov", "senate.gov", "uscourts.gov", "law.cornell.edu",
            "justice.gov", "eeoc.gov", "dol.gov", "hud.gov", "cfpb.gov"
        },
        Jurisdiction.US_CA: {
            "ca.gov", "leginfo.legislature.ca.gov", "courts.ca.gov",
            "dca.ca.gov", "hcd.ca.gov", "dfpi.ca.gov"
        },
        Jurisdiction.US_NY: {
            "ny.gov", "nycourts.gov", "nyassembly.gov", "nysenate.gov",
            "ag.ny.gov", "dfs.ny.gov"
        },
        Jurisdiction.US_TX: {
            "texas.gov", "tlo.texas.gov", "txcourts.gov",
            "oag.texas.gov", "tdi.texas.gov"
        },
        Jurisdiction.UK: {
            "gov.uk", "legislation.gov.uk", "bailii.org",
            "judiciary.uk", "parliament.uk"
        },
        Jurisdiction.CA_FEDERAL: {
            "canada.ca", "laws-lois.justice.gc.ca", "scc-csc.ca",
            "fct-cf.gc.ca"
        },
        Jurisdiction.CA_ON: {
            "ontario.ca", "ola.org", "canlii.org"
        },
        Jurisdiction.AU_FEDERAL: {
            "gov.au", "legislation.gov.au", "austlii.edu.au",
            "hcourt.gov.au"
        },
        Jurisdiction.EU: {
            "europa.eu", "eur-lex.europa.eu", "curia.europa.eu",
            "edps.europa.eu"
        },
    }
    
    # Source type to authority mapping
    TYPE_AUTHORITY = {
        SourceType.STATUTE: SourceAuthority.PRIMARY,
        SourceType.REGULATION: SourceAuthority.PRIMARY,
        SourceType.CASE_LAW: SourceAuthority.PRIMARY,
        SourceType.COURT_RULE: SourceAuthority.PRIMARY,
        SourceType.GOVERNMENT_PUBLICATION: SourceAuthority.OFFICIAL,
        SourceType.LEGAL_AID_RESOURCE: SourceAuthority.TERTIARY,
        SourceType.UNKNOWN: SourceAuthority.UNVERIFIED,
    }
    
    def __init__(self):
        self._source_metadata: Dict[str, SourceMetadata] = {}
        self._verified_cache: Set[str] = set()
    
    def verify_source(self, source: Source) -> SourceMetadata:
        """
        Verify a source and return metadata.
        In production, this would check against a database of verified sources.
        """
        source_id = self._generate_source_id(source)
        
        if source_id in self._source_metadata:
            return self._source_metadata[source_id]
        
        # Determine authority from source type
        authority = self.TYPE_AUTHORITY.get(source.type, SourceAuthority.UNVERIFIED)
        
        # Check domain authority
        domain_authority = self._check_domain_authority(source.url, source.jurisdiction)
        if domain_authority and authority == SourceAuthority.UNVERIFIED:
            authority = domain_authority
        
        # Calculate quality scores
        authority_score = self._calculate_authority_score(authority)
        currency_score = self._calculate_currency_score(source)
        relevance_score = 1.0  # Would be calculated based on query match
        
        metadata = SourceMetadata(
            source_id=source_id,
            authority=authority,
            publisher=self._extract_publisher(source.url),
            authority_score=authority_score,
            currency_score=currency_score,
            relevance_score=relevance_score,
        )
        
        # Mark as verified if high authority and official domain
        if authority in (SourceAuthority.PRIMARY, SourceAuthority.OFFICIAL) and domain_authority:
            source.verified = True
            self._verified_cache.add(source_id)
            metadata.verification_method = "automated_domain_check"
            metadata.last_verified = datetime.utcnow()
        
        self._source_metadata[source_id] = metadata
        return metadata
    
    def _generate_source_id(self, source: Source) -> str:
        """Generate unique ID for a source"""
        import hashlib
        content = f"{source.title}|{source.citation}|{source.url}|{source.jurisdiction.value}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _check_domain_authority(self, url: Optional[str], jurisdiction: Jurisdiction) -> Optional[SourceAuthority]:
        """Check if URL is from an official domain"""
        if not url:
            return None
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            
            official_domains = self.OFFICIAL_DOMAINS.get(jurisdiction, set())
            
            for official_domain in official_domains:
                if domain.endswith(official_domain):
                    return SourceAuthority.OFFICIAL
        except Exception:
            pass
        
        return None
    
    def _extract_publisher(self, url: Optional[str]) -> str:
        """Extract publisher name from URL"""
        if not url:
            return "Unknown"
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
            return domain
        except Exception:
            return "Unknown"
    
    def _calculate_authority_score(self, authority: SourceAuthority) -> float:
        scores = {
            SourceAuthority.PRIMARY: 1.0,
            SourceAuthority.OFFICIAL: 0.9,
            SourceAuthority.SECONDARY: 0.7,
            SourceAuthority.TERTIARY: 0.5,
            SourceAuthority.UNVERIFIED: 0.2,
        }
        return scores.get(authority, 0.2)
    
    def _calculate_currency_score(self, source: Source) -> float:
        """Calculate how current the source likely is"""
        # In production, would check actual publication/verification dates
        if source.verified:
            return 1.0
        return 0.5
    
    def is_verified(self, source: Source) -> bool:
        """Check if a source has been verified"""
        source_id = self._generate_source_id(source)
        return source_id in self._verified_cache
    
    def get_metadata(self, source: Source) -> Optional[SourceMetadata]:
        """Get metadata for a source"""
        source_id = self._generate_source_id(source)
        return self._source_metadata.get(source_id)
    
    def filter_verified(self, sources: List[Source]) -> List[Source]:
        """Filter to only verified sources"""
        return [s for s in sources if s.verified]
    
    def rank_sources(self, sources: List[Source], query_category: Optional[LegalCategory] = None) -> List[Source]:
        """Rank sources by quality and relevance"""
        scored = []
        for source in sources:
            metadata = self.verify_source(source)
            quality = metadata.overall_quality
            
            # Boost relevance for matching category
            if query_category and query_category.value in metadata.applies_to_categories:
                quality += 0.1
            
            scored.append((quality, source))
        
        # Sort by quality descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored]


class SourceRepository:
    """Manages the collection of verified legal sources"""
    
    def __init__(self):
        self.verifier = SourceVerifier()
        self._sources: List[Source] = []
        self._by_jurisdiction: Dict[Jurisdiction, List[Source]] = {}
        self._by_category: Dict[LegalCategory, List[Source]] = {}
        self._initialize_default_sources()
    
    def _initialize_default_sources(self):
        """Initialize with the default verified sources"""
        from app.services.constants import VERIFIED_SOURCES as DEFAULT_SOURCES
        
        for jurisdiction, sources in DEFAULT_SOURCES.items():
            for source in sources:
                self.add_source(source)
    
    def add_source(self, source: Source) -> SourceMetadata:
        """Add a source to the repository"""
        metadata = self.verifier.verify_source(source)
        self._sources.append(source)
        
        # Index by jurisdiction
        if source.jurisdiction not in self._by_jurisdiction:
            self._by_jurisdiction[source.jurisdiction] = []
        self._by_jurisdiction[source.jurisdiction].append(source)
        
        # Index by category (if applicable)
        # In production, would have category mapping
        
        return metadata
    
    def get_sources(
        self,
        jurisdiction: Jurisdiction,
        legal_category: Optional[LegalCategory] = None,
        verified_only: bool = True,
        max_results: int = 10,
    ) -> List[Source]:
        """Get sources for a jurisdiction and optional category"""
        sources = self._by_jurisdiction.get(jurisdiction, [])
        
        # Add federal sources for US states
        if jurisdiction in [Jurisdiction.US_CA, Jurisdiction.US_NY, Jurisdiction.US_TX]:
            sources = sources + self._by_jurisdiction.get(Jurisdiction.US_FEDERAL, [])
        
        if verified_only:
            sources = self.verifier.filter_verified(sources)
        
        if legal_category:
            sources = self.verifier.rank_sources(sources, legal_category)
        else:
            sources = self.verifier.rank_sources(sources)
        
        return sources[:max_results]
    
    def get_source_by_id(self, source_id: str) -> Optional[Source]:
        """Get a source by its ID"""
        for source in self._sources:
            if self.verifier._generate_source_id(source) == source_id:
                return source
        return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics"""
        verified_count = len(self.verifier.filter_verified(self._sources))
        by_jurisdiction = {
            j.value: len(sources)
            for j, sources in self._by_jurisdiction.items()
        }
        by_type = {}
        for source in self._sources:
            by_type[source.type.value] = by_type.get(source.type.value, 0) + 1
        
        return {
            "total_sources": len(self._sources),
            "verified_sources": verified_count,
            "verification_rate": verified_count / len(self._sources) if self._sources else 0,
            "by_jurisdiction": by_jurisdiction,
            "by_type": by_type,
        }


# Global source repository instance
_source_repository: Optional[SourceRepository] = None


def get_source_repository() -> SourceRepository:
    """Get global source repository instance"""
    global _source_repository
    if _source_repository is None:
        _source_repository = SourceRepository()
    return _source_repository


def create_source_repository() -> SourceRepository:
    """Factory function for source repository"""
    return SourceRepository()