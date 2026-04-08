"""Oracle agent for multilingual web research and document extraction."""

import time
from typing import List, Dict, Any, Optional
from sagascout.core.base_agent import BaseAgent


class Oracle(BaseAgent):
    """
    Oracle agent specializes in multilingual research and document extraction.
    
    Capabilities:
    - Multilingual web research across countries and archives
    - Document extraction and evidence gathering
    - Cross-border historical research
    - Archive navigation and record discovery
    """

    def __init__(self, name: str = "Oracle", config: Dict[str, Any] = None):
        """
        Initialize Oracle agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary. Supported keys:
                - live_search (bool): Enable real HTTP research (default: False)
                - translation_provider (str): 'google' or None for stub (default: None)
                - archive_search_result_count (int): Fixed result count for stub
                  archive searches; uses realistic defaults when not set
        """
        super().__init__(name, config)
        self.supported_languages = [
            "en", "es", "fr", "de", "it", "pt", "nl", "sv", "no", "da",
            "pl", "ru", "zh", "ja", "ko", "ar", "he",
        ]
        self.research_cache = {}
        self.documents = []

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process research or extraction request.

        Args:
            input_data: Dictionary containing research parameters
                - action: 'research', 'extract', or 'translate'
                - query: Search query or document text
                - languages: List of target languages
                - countries: List of target countries

        Returns:
            Dictionary with research results
        """
        action = input_data.get("action")
        
        if action == "research":
            result = self.research(input_data)
        elif action == "extract":
            result = self.extract_document(input_data)
        elif action == "translate":
            result = self.translate_query(input_data)
        elif action == "search_archives":
            result = self.search_archives(input_data)
        else:
            result = {"error": f"Unknown action: {action}"}

        # Remember this research
        self.remember({
            "event": "research_operation",
            "action": action,
            "timestamp": input_data.get("timestamp", "unknown"),
        })

        return result

    def research(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct multilingual research.

        When ``config['live_search']`` is ``True``, performs real HTTP searches
        using the FamilySearch public search interface. Otherwise returns
        deterministic stub results suitable for testing.

        Args:
            request: Research request with query and parameters

        Returns:
            Research results
        """
        query = request.get("query", "")
        languages = request.get("languages", ["en"])
        countries = request.get("countries", [])

        # Check cache
        cache_key = f"{query}:{','.join(languages)}:{','.join(countries)}"
        if cache_key in self.research_cache:
            return {
                "status": "cached",
                "results": self.research_cache[cache_key],
            }

        results = []
        for lang in languages:
            if lang in self.supported_languages:
                if self.config.get("live_search"):
                    sources = self._live_search(query, lang, countries)
                else:
                    sources = self._generate_sources(query, lang, countries)
                result = {
                    "language": lang,
                    "query": query,
                    "sources": sources,
                    "summary": f"Research results for '{query}' in {lang}",
                }
                results.append(result)

        # Cache results
        self.research_cache[cache_key] = results

        return {
            "status": "success",
            "query": query,
            "languages": languages,
            "results": results,
            "total_sources": sum(len(r["sources"]) for r in results),
        }

    def _live_search(
        self, query: str, language: str, countries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Perform a real HTTP search for genealogical records.

        Uses the FamilySearch public catalog search endpoint. Retries up to
        3 times with exponential back-off on transient HTTP errors.

        Args:
            query: Search query string
            language: BCP-47 language code
            countries: List of ISO 3166-1 alpha-2 country codes

        Returns:
            List of source dictionaries
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return self._generate_sources(query, language, countries)

        url = "https://www.familysearch.org/search/catalog"
        params = {"q": query, "lang": language}
        if countries:
            params["places"] = ",".join(countries)

        sources = []
        for attempt in range(3):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                for link in soup.select("a[href]")[:4]:
                    href = link.get("href", "")
                    if href.startswith("/"):
                        href = f"https://www.familysearch.org{href}"
                    sources.append({
                        "id": f"live_{language}_{len(sources)}",
                        "language": language,
                        "type": "archive",
                        "reliability": 0.9,
                        "url": href,
                        "title": link.get_text(strip=True),
                    })
                break
            except Exception:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    # Fall back to stubs on persistent failure
                    return self._generate_sources(query, language, countries)

        return sources if sources else self._generate_sources(
            query, language, countries
        )

    def extract_document(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract information from a document.

        Args:
            request: Document extraction request

        Returns:
            Extracted information
        """
        document = request.get("document", {})
        extraction_type = request.get("type", "general")

        extracted = {
            "document_id": document.get("id"),
            "type": extraction_type,
            "data": {},
        }

        if extraction_type == "birth_record":
            extracted["data"] = self._extract_birth_record(document)
        elif extraction_type == "death_record":
            extracted["data"] = self._extract_death_record(document)
        elif extraction_type == "marriage_record":
            extracted["data"] = self._extract_marriage_record(document)
        elif extraction_type == "census":
            extracted["data"] = self._extract_census(document)
        else:
            extracted["data"] = self._extract_general(document)

        # Store document
        self.documents.append(extracted)

        return {
            "status": "success",
            "extracted": extracted,
            "confidence": self._calculate_extraction_confidence(extracted),
        }

    def translate_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translate a query into multiple languages.

        When ``config['translation_provider']`` is ``'google'``, uses the
        ``deep-translator`` library to perform real translations via Google
        Translate (no API key required for the free tier). Otherwise returns
        stub translations prefixed with the language code.

        Args:
            request: Translation request

        Returns:
            Translations
        """
        query = request.get("query", "")
        target_languages = request.get("languages", self.supported_languages)
        provider = self.config.get("translation_provider")

        translations = {}
        for lang in target_languages:
            if lang not in self.supported_languages:
                continue
            if provider == "google":
                translated_text = self._translate_with_google(query, lang)
            else:
                # Deterministic stub: prefix with language code
                translated_text = f"[{lang}] {query}"
            translations[lang] = {
                "original": query,
                "translated": translated_text,
                "language": lang,
            }

        return {
            "status": "success",
            "original": query,
            "translations": translations,
        }

    def search_archives(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search across multiple archives.

        Args:
            request: Archive search request

        Returns:
            Search results from archives
        """
        query = request.get("query", "")
        archives = request.get("archives", [])
        countries = request.get("countries", [])

        results = []
        
        # Supported archives by country
        archive_map = {
            "US": ["Ancestry.com", "FamilySearch", "MyHeritage"],
            "UK": ["FindMyPast", "TheGenealogist", "FreeBMD"],
            "FR": ["Archives Nationales", "Geneanet"],
            "DE": ["Archion", "Ancestry.de"],
            "IT": ["Antenati", "FamilySearch"],
            "ES": ["Pares", "FamilySearch"],
        }

        for country in countries:
            country_archives = archive_map.get(country, [])
            for archive in country_archives:
                if not archives or archive in archives:
                    result = {
                        "archive": archive,
                        "country": country,
                        "query": query,
                        "records_found": self._simulate_archive_search(
                            archive, query
                        ),
                    }
                    results.append(result)

        return {
            "status": "success",
            "query": query,
            "archives_searched": len(results),
            "results": results,
            "total_records": sum(r["records_found"] for r in results),
        }

    def _generate_sources(
        self, query: str, language: str, countries: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate simulated research sources."""
        sources = []
        
        base_sources = [
            {"type": "archive", "reliability": 0.9},
            {"type": "genealogy_site", "reliability": 0.8},
            {"type": "historical_record", "reliability": 0.95},
            {"type": "newspaper", "reliability": 0.7},
        ]

        for idx, base in enumerate(base_sources):
            source = {
                "id": f"src_{language}_{idx}",
                "language": language,
                "type": base["type"],
                "reliability": base["reliability"],
                "url": f"https://example.com/{language}/source{idx}",
            }
            # Tailor source based on countries if provided
            if countries:
                source["countries"] = countries
                source["url"] = f"https://example.com/{language}/{countries[0]}/source{idx}"
            sources.append(source)

        return sources

    def _extract_document_fields(
        self, document: Dict[str, Any], field_mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Extract fields from document using a field mapping.

        Args:
            document: Document to extract from
            field_mapping: Dictionary mapping output field names to document keys

        Returns:
            Dictionary with extracted fields
        """
        result = {}
        for output_key, doc_key in field_mapping.items():
            if doc_key.endswith("[]"):
                # Handle default empty list
                result[output_key] = document.get(doc_key[:-2], [])
            elif doc_key.endswith("{}"):
                # Handle default empty dict
                result[output_key] = document.get(doc_key[:-2], {})
            else:
                result[output_key] = document.get(doc_key)
        return result

    def _extract_birth_record(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a birth record."""
        fields = self._extract_document_fields(document, {
            "name": "name",
            "birth_date": "date",
            "birth_place": "place",
            "parents": "parents[]",
        })
        fields["record_type"] = "birth"
        return fields

    def _extract_death_record(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a death record."""
        fields = self._extract_document_fields(document, {
            "name": "name",
            "death_date": "date",
            "death_place": "place",
            "age": "age",
        })
        fields["record_type"] = "death"
        return fields

    def _extract_marriage_record(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a marriage record."""
        fields = self._extract_document_fields(document, {
            "spouse1": "spouse1",
            "spouse2": "spouse2",
            "marriage_date": "date",
            "marriage_place": "place",
        })
        fields["record_type"] = "marriage"
        return fields

    def _extract_census(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract data from a census record."""
        fields = self._extract_document_fields(document, {
            "year": "year",
            "household": "household[]",
            "location": "location",
        })
        fields["record_type"] = "census"
        return fields

    def _extract_general(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Extract general information from a document."""
        fields = self._extract_document_fields(document, {
            "content": "content",
            "metadata": "metadata{}",
        })
        fields["record_type"] = "general"
        return fields

    def _calculate_extraction_confidence(
        self, extracted: Dict[str, Any]
    ) -> float:
        """Calculate confidence in extraction."""
        data = extracted.get("data", {})
        
        # Count non-empty fields
        filled_fields = sum(1 for v in data.values() if v)
        total_fields = len(data)
        
        if total_fields == 0:
            return 0.0
        
        return (filled_fields / total_fields) * 100

    def _translate_with_google(self, text: str, target_lang: str) -> str:
        """
        Translate text using Google Translate via deep-translator.

        Falls back to stub on import error or translation failure.

        Args:
            text: Text to translate
            target_lang: BCP-47 language code

        Returns:
            Translated text string
        """
        try:
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source="auto", target=target_lang).translate(text)
        except Exception:
            return f"[{target_lang}] {text}"

    def _simulate_archive_search(self, archive: str, query: str) -> int:
        """
        Return a deterministic stub result count for an archive search.

        The count is derived from the lengths of the archive and query strings
        so the value is stable across test runs. The ``archive_search_result_count``
        config key can override this to a fixed value.

        Args:
            archive: Archive name
            query: Search query

        Returns:
            Simulated record count (0–50)
        """
        if "archive_search_result_count" in self.config:
            return int(self.config["archive_search_result_count"])
        # Deterministic hash-based stub: 0-50 range
        return (len(archive) + len(query)) % 51

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return self.supported_languages

    def get_documents(self) -> List[Dict[str, Any]]:
        """Get all extracted documents."""
        return self.documents