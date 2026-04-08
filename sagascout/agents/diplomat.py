"""Diplomat agent for outreach and cross-cultural communication."""

import copy
from typing import List, Dict, Any, Optional
from sagascout.core.base_agent import BaseAgent


class Diplomat(BaseAgent):
    """
    Diplomat agent specializes in outreach and cross-cultural communication.
    
    Capabilities:
    - Initial outreach and communication with DNA matches
    - Cross-border, cross-cultural reasoning
    - Message composition in multiple languages
    - Cultural sensitivity and etiquette
    """

    def __init__(self, name: str = "Diplomat", config: Dict[str, Any] = None):
        """
        Initialize Diplomat agent.

        Args:
            name: Name of the agent
            config: Configuration dictionary
        """
        super().__init__(name, config)
        self.communications = []
        self.contacts = {}
        self.cultural_profiles = self._load_cultural_profiles()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process communication request.

        Args:
            input_data: Dictionary containing communication parameters
                - action: 'draft', 'send', 'respond', or 'analyze'
                - data: Relevant data for the action

        Returns:
            Dictionary with processing results
        """
        action = input_data.get("action")
        
        if action == "draft":
            result = self.draft_message(input_data)
        elif action == "send":
            result = self.send_message(input_data)
        elif action == "respond":
            result = self.respond_to_message(input_data)
        elif action == "analyze_culture":
            result = self.analyze_cultural_context(input_data)
        else:
            result = {"error": f"Unknown action: {action}"}

        # Remember this communication
        self.remember({
            "event": "communication",
            "action": action,
            "timestamp": input_data.get("timestamp", "unknown"),
        })

        return result

    def draft_message(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draft an outreach message.

        When ``config['llm_api_key']`` and optionally ``config['llm_model']``
        are set, uses an OpenAI-compatible API to generate a culturally nuanced
        message. Falls back to template-based drafting on any error or when the
        config keys are absent.

        Args:
            request: Message draft request

        Returns:
            Drafted message
        """
        recipient = request.get("recipient", {})
        purpose = request.get("purpose", "initial_contact")
        language = request.get("language", "en")
        context = request.get("context", {})

        # Get cultural profile
        country = recipient.get("country", "US")
        cultural_notes = self.cultural_profiles.get(country, {})

        # Try LLM drafting if configured; fall back to templates
        if self.config.get("llm_api_key"):
            message = self._compose_message_with_llm(
                purpose, language, context, cultural_notes,
                recipient, request
            ) or self._compose_message(purpose, language, context, cultural_notes)
        else:
            message = self._compose_message(
                purpose, language, context, cultural_notes
            )

        draft = {
            "recipient": recipient,
            "language": language,
            "purpose": purpose,
            "subject": message["subject"],
            "body": message["body"],
            "cultural_notes": cultural_notes,
            "tone": message["tone"],
        }

        return {
            "status": "success",
            "draft": draft,
            "recommendations": self._generate_recommendations(
                draft, cultural_notes
            ),
        }

    def draft_with_llm(
        self, request: Dict[str, Any], llm_client: Any = None
    ) -> Dict[str, Any]:
        """
        Draft a message using an OpenAI-compatible client object.

        This is an explicit alternative to :meth:`draft_message` that accepts
        a pre-instantiated client rather than reading credentials from config.

        Args:
            request: Message draft request (same format as :meth:`draft_message`)
            llm_client: An object with a ``chat.completions.create`` method
                        (e.g. ``openai.OpenAI()``). Falls back to template
                        drafting when ``None``.

        Returns:
            Drafted message result
        """
        recipient = request.get("recipient", {})
        purpose = request.get("purpose", "initial_contact")
        language = request.get("language", "en")
        context = request.get("context", {})
        country = recipient.get("country", "US")
        cultural_notes = self.cultural_profiles.get(country, {})

        message = None
        if llm_client is not None:
            message = self._call_llm_client(
                llm_client, purpose, language, context, cultural_notes, recipient
            )
        if message is None:
            message = self._compose_message(purpose, language, context, cultural_notes)

        draft = {
            "recipient": recipient,
            "language": language,
            "purpose": purpose,
            "subject": message["subject"],
            "body": message["body"],
            "cultural_notes": cultural_notes,
            "tone": message["tone"],
        }
        return {
            "status": "success",
            "draft": draft,
            "recommendations": self._generate_recommendations(draft, cultural_notes),
        }

    def send_message(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a message to a contact.

        Args:
            request: Message send request

        Returns:
            Send confirmation
        """
        message = request.get("message", {})
        recipient_id = message.get("recipient", {}).get("id")

        # Store communication
        communication = {
            "id": f"comm_{len(self.communications)}",
            "recipient_id": recipient_id,
            "message": message,
            "status": "sent",
            "timestamp": request.get("timestamp", "unknown"),
        }
        self.communications.append(communication)

        # Update contact
        if recipient_id not in self.contacts:
            self.contacts[recipient_id] = {
                "id": recipient_id,
                "messages_sent": 0,
                "messages_received": 0,
                "last_contact": None,
            }
        
        self.contacts[recipient_id]["messages_sent"] += 1
        self.contacts[recipient_id]["last_contact"] = communication["timestamp"]

        return {
            "status": "success",
            "communication_id": communication["id"],
            "recipient_id": recipient_id,
        }

    def respond_to_message(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Respond to a received message.

        Args:
            request: Response request

        Returns:
            Response draft
        """
        original_message = request.get("original_message", {})
        response_tone = request.get("tone", "friendly")

        # Analyze original message
        analysis = self._analyze_message(original_message)

        # Generate response
        response = self._generate_response(
            original_message, analysis, response_tone
        )

        return {
            "status": "success",
            "response": response,
            "analysis": analysis,
        }

    def analyze_cultural_context(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze cultural context for communication.

        Args:
            request: Cultural analysis request

        Returns:
            Cultural analysis
        """
        country = request.get("country")
        situation = request.get("situation", "general")

        if country not in self.cultural_profiles:
            return {
                "status": "limited",
                "country": country,
                "message": "Limited cultural information available",
            }

        profile = self.cultural_profiles[country]
        
        analysis = {
            "country": country,
            "communication_style": profile.get("communication_style"),
            "formality_level": profile.get("formality_level"),
            "greeting_customs": profile.get("greeting_customs"),
            "taboo_topics": profile.get("taboo_topics", []),
            "best_practices": profile.get("best_practices", []),
        }

        return {
            "status": "success",
            "analysis": analysis,
            "recommendations": self._generate_cultural_recommendations(
                profile, situation
            ),
        }

    def _compose_message(
        self,
        purpose: str,
        language: str,
        context: Dict[str, Any],
        cultural_notes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compose a message based on purpose and context."""
        templates = {
            "initial_contact": {
                "subject": "Genealogy Connection",
                "body": (
                    "Hello,\n\n"
                    "I hope this message finds you well. I am researching my family "
                    "history and noticed we share DNA matches. I would be delighted to "
                    "connect and share information about our common ancestors.\n\n"
                    "Best regards"
                ),
                "tone": "friendly_formal",
            },
            "share_research": {
                "subject": "Research Findings to Share",
                "body": (
                    "Hello,\n\n"
                    "I wanted to share some recent genealogy research findings that "
                    "may be relevant to your family tree. I've attached details about "
                    "several ancestors we have in common.\n\n"
                    "Looking forward to hearing from you"
                ),
                "tone": "informative",
            },
            "request_information": {
                "subject": "Question About Family History",
                "body": (
                    "Hello,\n\n"
                    "I am working on documenting our family history and was wondering "
                    "if you might have information about [specific ancestor or branch]. "
                    "Any details you could share would be greatly appreciated.\n\n"
                    "Thank you for your time"
                ),
                "tone": "respectful",
            },
        }

        template = copy.deepcopy(templates.get(purpose, templates["initial_contact"]))
        
        # Adjust for cultural context
        if cultural_notes.get("formality_level") == "high":
            template["body"] = template["body"].replace("Hello", "Dear Sir/Madam")

        return template

    def _generate_recommendations(
        self, draft: Dict[str, Any], cultural_notes: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving the message."""
        recommendations = []

        # Check formality
        if cultural_notes.get("formality_level") == "high":
            recommendations.append(
                "Consider using more formal language and titles"
            )

        # Check length
        if cultural_notes.get("communication_style") == "direct":
            recommendations.append(
                "Keep message concise and to the point"
            )
        elif cultural_notes.get("communication_style") == "indirect":
            recommendations.append(
                "Consider adding more context and background information"
            )

        # General recommendations
        recommendations.append("Include specific connection details (shared ancestor, DNA match)")
        recommendations.append("Be respectful of privacy and cultural sensitivities")

        return recommendations

    def _analyze_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a received message."""
        text = message.get("text", "")
        
        # Analyze tone
        tone = "neutral"
        if any(word in text.lower() for word in ["excited", "wonderful", "great"]):
            tone = "positive"
        elif any(word in text.lower() for word in ["concerned", "confused"]):
            tone = "cautious"

        # Analyze intent
        intent = "general"
        if "?" in text:
            intent = "question"
        elif any(word in text.lower() for word in ["share", "found", "discovered"]):
            intent = "information_sharing"

        return {
            "tone": tone,
            "intent": intent,
            "length": len(text),
            "language": message.get("language", "en"),
        }

    def _generate_response(
        self,
        original: Dict[str, Any],
        analysis: Dict[str, Any],
        tone: str,
    ) -> Dict[str, Any]:
        """Generate a response to a message."""
        response_templates = {
            "question": (
                "Thank you for your message. Regarding your question, I would be "
                "happy to provide more information..."
            ),
            "information_sharing": (
                "Thank you for sharing this information! This is very helpful "
                "for my research..."
            ),
            "general": (
                "Thank you for reaching out. I appreciate your interest in "
                "connecting about our family history..."
            ),
        }

        intent = analysis.get("intent", "general")
        body = response_templates.get(intent, response_templates["general"])

        return {
            "subject": f"Re: {original.get('subject', 'Family History')}",
            "body": body,
            "tone": tone,
            "language": original.get("language", "en"),
        }

    def _generate_cultural_recommendations(
        self, profile: Dict[str, Any], situation: str
    ) -> List[str]:
        """Generate cultural recommendations."""
        recommendations = []

        style = profile.get("communication_style")
        if style == "direct":
            recommendations.append("Be clear and concise in communication")
        elif style == "indirect":
            recommendations.append("Use context and build relationships gradually")

        formality = profile.get("formality_level")
        if formality == "high":
            recommendations.append("Use formal titles and honorifics")
            recommendations.append("Show respect for hierarchy and tradition")

        recommendations.extend(profile.get("best_practices", []))

        return recommendations

    def _load_cultural_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Load cultural communication profiles."""
        return {
            "US": {
                "communication_style": "direct",
                "formality_level": "medium",
                "greeting_customs": "Casual greetings acceptable",
                "taboo_topics": ["politics", "religion"],
                "best_practices": [
                    "Be friendly and personable",
                    "Get to the point quickly",
                ],
            },
            "UK": {
                "communication_style": "indirect",
                "formality_level": "medium-high",
                "greeting_customs": "Polite and reserved",
                "taboo_topics": ["money", "politics"],
                "best_practices": [
                    "Use proper etiquette",
                    "Avoid being too direct",
                ],
            },
            "JP": {
                "communication_style": "indirect",
                "formality_level": "high",
                "greeting_customs": "Formal bows and titles",
                "taboo_topics": ["direct confrontation"],
                "best_practices": [
                    "Show great respect",
                    "Build relationship slowly",
                    "Use honorifics appropriately",
                ],
            },
            "DE": {
                "communication_style": "direct",
                "formality_level": "high",
                "greeting_customs": "Formal titles important",
                "taboo_topics": ["WWII unless relevant"],
                "best_practices": [
                    "Be punctual and organized",
                    "Use formal address until invited otherwise",
                ],
            },
            "FR": {
                "communication_style": "indirect",
                "formality_level": "high",
                "greeting_customs": "Formal greetings essential",
                "taboo_topics": ["money", "personal questions"],
                "best_practices": [
                    "Use formal language initially",
                    "Show cultural awareness",
                ],
            },
        }

    def get_communication_history(
        self, contact_id: str = None
    ) -> List[Dict[str, Any]]:
        """Get communication history, optionally filtered by contact."""
        if contact_id:
            return [
                c for c in self.communications
                if c.get("recipient_id") == contact_id
            ]
        return self.communications

    def get_contact_info(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a contact."""
        return self.contacts.get(contact_id)

    # ------------------------------------------------------------------ #
    # LLM helpers                                                          #
    # ------------------------------------------------------------------ #

    def _compose_message_with_llm(
        self,
        purpose: str,
        language: str,
        context: Dict[str, Any],
        cultural_notes: Dict[str, Any],
        recipient: Dict[str, Any],
        request: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Compose a message using an OpenAI-compatible API configured via
        ``config['llm_api_key']`` and optionally ``config['llm_model']``.

        Returns ``None`` on any failure so the caller can fall back to templates.
        """
        try:
            import openai
            client = openai.OpenAI(api_key=self.config["llm_api_key"])
            return self._call_llm_client(
                client, purpose, language, context, cultural_notes, recipient
            )
        except Exception:
            return None

    def _call_llm_client(
        self,
        client: Any,
        purpose: str,
        language: str,
        context: Dict[str, Any],
        cultural_notes: Dict[str, Any],
        recipient: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Call an OpenAI-compatible ``chat.completions.create`` method to draft
        a genealogy outreach message.

        Returns a message dict on success, ``None`` on any failure.
        """
        model = self.config.get("llm_model", "gpt-3.5-turbo")
        formality = cultural_notes.get("formality_level", "medium")
        comm_style = cultural_notes.get("communication_style", "direct")
        system_prompt = (
            "You are a genealogy communication expert. "
            "Draft concise, culturally appropriate outreach messages."
        )
        user_prompt = (
            f"Draft a genealogy message.\n"
            f"Purpose: {purpose}\n"
            f"Language: {language}\n"
            f"Recipient country: {recipient.get('country', 'US')}\n"
            f"Formality: {formality}\n"
            f"Communication style: {comm_style}\n"
            f"Context: {context}\n\n"
            "Return ONLY a JSON object with keys 'subject', 'body', and 'tone'."
        )
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            import json as _json
            content = response.choices[0].message.content.strip()
            # Strip markdown fences if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            parsed = _json.loads(content)
            if all(k in parsed for k in ("subject", "body", "tone")):
                return parsed
        except Exception:
            pass
        return None
