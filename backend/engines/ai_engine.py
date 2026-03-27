"""
AI Engine for Sentinel - Groq-powered intelligence layer.
Provides natural language summaries and AI-generated DMCA notices.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv


load_dotenv()


class SentinelAI:
    """
    AI-powered intelligence layer for Sentinel piracy detection.
    Uses Groq API for fast, efficient LLM inference.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI engine.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Groq API key required. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Updated to latest stable model
    
    def generate_detection_summary(self, detection_data: Dict) -> str:
        """
        Generate a natural language summary of a detection event.
        
        Args:
            detection_data: Dictionary containing:
                - content_title: Name of protected content
                - platform: Where piracy was detected
                - confidence_score: Match confidence (0-100)
                - consistency_ratio: Temporal consistency (0-1)
                - temporal_location: Frame range where match was found
                - timestamp: When detection occurred
                
        Returns:
            Natural language summary string
            
        Example:
            >>> ai = SentinelAI()
            >>> summary = ai.generate_detection_summary({
            ...     'content_title': 'Super Bowl LVIII',
            ...     'platform': 'Twitch',
            ...     'confidence_score': 98.5,
            ...     'consistency_ratio': 0.95,
            ...     'temporal_location': {'start': 450, 'end': 550},
            ...     'timestamp': '2024-02-11T20:30:00Z'
            ... })
            >>> print(summary)
        """
        confidence_score = detection_data.get('confidence_score', 0)
        if not isinstance(confidence_score, (int, float)):
            confidence_score = 0.0

        consistency_ratio = detection_data.get('consistency_ratio', 0)
        if not isinstance(consistency_ratio, (int, float)):
            consistency_ratio = 0.0

        prompt = f"""You are Sentinel, an AI-powered piracy detection system. Generate a concise, professional summary of this detection event.

Detection Data:
- Protected Content: {detection_data.get('content_title', 'Unknown')}
- Platform: {detection_data.get('platform', 'Unknown')}
- Confidence Score: {confidence_score:.2f}%
- Temporal Consistency: {consistency_ratio:.2%}
- Match Location: Frames {detection_data.get('temporal_location', {}).get('start', 'N/A')}-{detection_data.get('temporal_location', {}).get('end', 'N/A')}
- Detected At: {detection_data.get('timestamp', 'Unknown')}

Generate a 2-3 sentence summary that:
1. States what was detected and where
2. Mentions the confidence level
3. Suggests immediate action if confidence is high (>90%)

Be professional, clear, and actionable."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Sentinel AI, a professional piracy detection assistant. Be concise and actionable."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Low temperature for consistent, factual output
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def generate_dmca_notice(self, detection_data: Dict, rights_holder: Dict) -> str:
        """
        Generate an AI-powered DMCA takedown notice.
        
        Args:
            detection_data: Dictionary containing detection information
            rights_holder: Dictionary containing:
                - name: Rights holder name
                - email: Contact email
                - address: Physical address
                - phone: Contact phone
                
        Returns:
            Formatted DMCA notice text
            
        Example:
            >>> ai = SentinelAI()
            >>> notice = ai.generate_dmca_notice(
            ...     detection_data={
            ...         'content_title': 'Super Bowl LVIII',
            ...         'platform': 'Twitch',
            ...         'stream_url': 'https://twitch.tv/pirate_stream',
            ...         'confidence_score': 98.5,
            ...         'timestamp': '2024-02-11T20:30:00Z'
            ...     },
            ...     rights_holder={
            ...         'name': 'NFL',
            ...         'email': 'legal@nfl.com',
            ...         'address': '345 Park Avenue, New York, NY 10154',
            ...         'phone': '+1-212-450-2000'
            ...     }
            ... )
        """
        prompt = f"""Generate a professional DMCA takedown notice based on this piracy detection.

DETECTION INFORMATION:
- Protected Work: {detection_data.get('content_title', 'Unknown')}
- Infringing Platform: {detection_data.get('platform', 'Unknown')}
- Infringing URL: {detection_data.get('stream_url', 'Not provided')}
- Detection Confidence: {detection_data.get('confidence_score', 0):.2f}%
- Detection Time: {detection_data.get('timestamp', 'Unknown')}

RIGHTS HOLDER INFORMATION:
- Name: {rights_holder.get('name', 'Unknown')}
- Email: {rights_holder.get('email', 'Unknown')}
- Address: {rights_holder.get('address', 'Unknown')}
- Phone: {rights_holder.get('phone', 'Unknown')}

Generate a formal DMCA notice following the Digital Millennium Copyright Act requirements. Include:
1. Identification of the copyrighted work
2. Identification of the infringing material and its location
3. Statement of good faith belief
4. Statement under penalty of perjury
5. Contact information
6. Physical or electronic signature placeholder

Use formal legal language. Be specific about the detection technology used (perceptual hashing, temporal matching)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal document assistant specializing in DMCA notices. Generate professional, legally compliant documents."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Very low temperature for formal legal text
                max_tokens=1000
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating DMCA notice: {str(e)}"
    
    def analyze_detection_pattern(self, detections: List[Dict]) -> str:
        """
        Analyze multiple detections to identify patterns and trends.
        
        Args:
            detections: List of detection event dictionaries
            
        Returns:
            Analysis summary with insights and recommendations
            
        Example:
            >>> ai = SentinelAI()
            >>> analysis = ai.analyze_detection_pattern([
            ...     {'platform': 'Twitch', 'confidence': 98.5, 'timestamp': '2024-02-11T20:30:00Z'},
            ...     {'platform': 'Twitch', 'confidence': 97.2, 'timestamp': '2024-02-11T20:45:00Z'},
            ...     {'platform': 'YouTube', 'confidence': 95.8, 'timestamp': '2024-02-11T21:00:00Z'}
            ... ])
        """
        if not detections:
            return "No detections to analyze."
        
        # Summarize detection data
        platforms = {}
        total_confidence = 0
        
        for det in detections:
            platform = det.get('platform', 'Unknown')
            platforms[platform] = platforms.get(platform, 0) + 1
            total_confidence += det.get('confidence_score', 0)
        
        avg_confidence = total_confidence / len(detections)
        
        prompt = f"""Analyze this piracy detection pattern and provide insights.

DETECTION SUMMARY:
- Total Detections: {len(detections)}
- Average Confidence: {avg_confidence:.2f}%
- Platform Distribution: {platforms}
- Time Range: {detections[0].get('timestamp', 'Unknown')} to {detections[-1].get('timestamp', 'Unknown')}

Provide:
1. Pattern identification (e.g., coordinated attack, single bad actor, etc.)
2. Platform-specific insights
3. Recommended actions
4. Priority level (Low/Medium/High/Critical)

Be concise (3-4 sentences)."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a security analyst specializing in piracy patterns. Provide actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error analyzing pattern: {str(e)}"
    
    def suggest_threshold_adjustment(self, false_positives: int, false_negatives: int, 
                                    current_threshold: float) -> Dict:
        """
        Use AI to suggest optimal threshold adjustments based on performance.
        
        Args:
            false_positives: Number of false positive detections
            false_negatives: Number of missed detections
            current_threshold: Current similarity threshold (0-100)
            
        Returns:
            Dictionary with suggested threshold and reasoning
        """
        prompt = f"""As a machine learning optimization expert, suggest threshold adjustments.

CURRENT PERFORMANCE:
- False Positives: {false_positives}
- False Negatives: {false_negatives}
- Current Threshold: {current_threshold}%

Analyze the trade-off and suggest:
1. New threshold value (0-100)
2. Brief reasoning (1-2 sentences)
3. Expected impact

Format response as JSON:
{{
    "suggested_threshold": <number>,
    "reasoning": "<string>",
    "expected_impact": "<string>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ML optimization expert. Provide data-driven recommendations in JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content.strip())
            return result
            
        except Exception as e:
            return {
                "suggested_threshold": current_threshold,
                "reasoning": f"Error: {str(e)}",
                "expected_impact": "No change recommended due to error"
            }


if __name__ == "__main__":
    print("Sentinel AI Engine - Test Mode")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("⚠ GROQ_API_KEY not set in environment")
        print("Set it with: export GROQ_API_KEY='your-key-here'")
        print("\nExample usage:")
        print("  ai = SentinelAI(api_key='your-key')")
        print("  summary = ai.generate_detection_summary(detection_data)")
    else:
        print("✓ GROQ_API_KEY found")
        print("✓ AI engine ready for use")
        print("\nAvailable methods:")
        print("  - generate_detection_summary()")
        print("  - generate_dmca_notice()")
        print("  - analyze_detection_pattern()")
        print("  - suggest_threshold_adjustment()")
    
    print("=" * 60)
