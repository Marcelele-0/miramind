import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from src.miramind.llm.langgraph.subgraphs import (
    build_angry_flow,
    build_excited_flow,
    build_gentle_flow,
    build_neutral_flow,
    build_sad_flow,
)


class TestSubgraphs:
    """Test suite for subgraph building functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_client = Mock()
        self.mock_tts_provider = Mock()
        self.mock_emotion_logger = Mock()

        self.test_state = {
            "user_input": "Test message",
            "emotion": "sad",
            "emotion_confidence": 0.85,
            "chat_history": [],
        }

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_build_sad_flow_structure(self, mock_generate_response):
        """Test sad flow graph structure."""
        mock_responder = Mock()
        mock_generate_response.return_value = mock_responder

        graph = build_sad_flow(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)

        # Verify graph structure
        assert graph is not None
        mock_generate_response.assert_called_once_with(
            "supportive and caring",
            self.mock_client,
            self.mock_tts_provider,
            self.mock_emotion_logger,
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_build_angry_flow_structure(self, mock_generate_response):
        """Test angry flow graph structure."""
        mock_responder = Mock()
        mock_generate_response.return_value = mock_responder

        graph = build_angry_flow(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)

        # Verify graph structure
        assert graph is not None
        mock_generate_response.assert_called_once_with(
            "calm and soothing", self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_build_excited_flow_structure(self, mock_generate_response):
        """Test excited flow graph structure."""
        mock_responder = Mock()
        mock_generate_response.return_value = mock_responder

        graph = build_excited_flow(
            self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )

        # Verify graph structure
        assert graph is not None
        mock_generate_response.assert_called_once_with(
            "enthusiastic and cheerful",
            self.mock_client,
            self.mock_tts_provider,
            self.mock_emotion_logger,
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_build_gentle_flow_structure(self, mock_generate_response):
        """Test gentle flow graph structure."""
        mock_responder = Mock()
        mock_generate_response.return_value = mock_responder

        graph = build_gentle_flow(
            self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )

        # Verify graph structure
        assert graph is not None
        mock_generate_response.assert_called_once_with(
            "gentle and reassuring",
            self.mock_client,
            self.mock_tts_provider,
            self.mock_emotion_logger,
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_build_neutral_flow_structure(self, mock_generate_response):
        """Test neutral flow graph structure."""
        mock_responder = Mock()
        mock_generate_response.return_value = mock_responder

        graph = build_neutral_flow(
            self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )

        # Verify graph structure
        assert graph is not None
        mock_generate_response.assert_called_once_with(
            "neutral and friendly",
            self.mock_client,
            self.mock_tts_provider,
            self.mock_emotion_logger,
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_sad_flow_with_follow_up(self, mock_generate_response):
        """Test sad flow includes follow-up functionality."""

        # Create a mock response function
        def mock_response_func(state):
            return {
                **state,
                "response": "I understand you're feeling sad.",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I understand you're feeling sad."},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        graph = build_sad_flow(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)
        compiled_graph = graph.compile()

        # Execute the graph
        result = compiled_graph.invoke(self.test_state)

        # Check that follow-up was added
        assert "Would you like to tell me more" in result["response"]
        assert len(result["chat_history"]) >= 2  # Original + follow-up

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_all_flows_return_compilable_graphs(self, mock_generate_response):
        """Test that all flow builders return compilable graphs."""

        def mock_response_func(state):
            return {**state, "response": "Test response"}

        mock_generate_response.return_value = mock_response_func

        flow_builders = [
            build_sad_flow,
            build_angry_flow,
            build_excited_flow,
            build_gentle_flow,
            build_neutral_flow,
        ]

        for builder in flow_builders:
            graph = builder(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)
            compiled_graph = graph.compile()

            # Should be able to invoke without errors
            result = compiled_graph.invoke(self.test_state)
            assert "response" in result

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_flow_state_preservation(self, mock_generate_response):
        """Test that flows preserve input state."""

        def mock_response_func(state):
            return {**state, "response": "Test response", "new_field": "added by flow"}

        mock_generate_response.return_value = mock_response_func

        input_state = {
            "user_input": "Hello",
            "emotion": "happy",
            "emotion_confidence": 0.9,
            "chat_history": [{"role": "user", "content": "Previous message"}],
            "custom_field": "should be preserved",
        }

        graph = build_excited_flow(
            self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        compiled_graph = graph.compile()

        result = compiled_graph.invoke(input_state)

        # Check that original state is preserved
        assert result["user_input"] == "Hello"
        assert result["emotion"] == "happy"
        assert result["emotion_confidence"] == 0.9
        assert result["custom_field"] == "should be preserved"

        # Check that new fields are added
        assert result["response"] == "Test response"
        assert result["new_field"] == "added by flow"

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_flow_error_handling(self, mock_generate_response):
        """Test flow behavior when response generation fails."""

        def mock_response_func(state):
            raise Exception("Response generation failed")

        mock_generate_response.return_value = mock_response_func

        graph = build_neutral_flow(
            self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
        )
        compiled_graph = graph.compile()

        # Should raise the exception (this is expected behavior)
        with pytest.raises(Exception, match="Response generation failed"):
            compiled_graph.invoke(self.test_state)

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_sad_flow_follow_up_message(self, mock_generate_response):
        """Test that sad flow properly adds follow-up message."""

        def mock_response_func(state):
            return {
                **state,
                "response": "I'm sorry to hear that.",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I'm sorry to hear that."},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        graph = build_sad_flow(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)
        compiled_graph = graph.compile()

        result = compiled_graph.invoke(self.test_state)

        # Check that follow-up is appended to response
        expected_followup = "Would you like to tell me more about what's making you feel this way?"
        assert expected_followup in result["response"]

        # Check that follow-up is also in chat history
        assert any(expected_followup in msg.get("content", "") for msg in result["chat_history"])

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_flow_response_styles(self, mock_generate_response):
        """Test that different flows use appropriate response styles."""

        def mock_response_func(state):
            return {**state, "response": "Test response"}

        mock_generate_response.return_value = mock_response_func

        # Test each flow with its expected style
        flow_styles = [
            (build_sad_flow, "supportive and caring"),
            (build_angry_flow, "calm and soothing"),
            (build_excited_flow, "enthusiastic and cheerful"),
            (build_gentle_flow, "gentle and reassuring"),
            (build_neutral_flow, "neutral and friendly"),
        ]

        for builder, expected_style in flow_styles:
            mock_generate_response.reset_mock()
            graph = builder(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)

            mock_generate_response.assert_called_once_with(
                expected_style, self.mock_client, self.mock_tts_provider, self.mock_emotion_logger
            )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_flow_client_parameters(self, mock_generate_response):
        """Test that flows properly pass client parameters."""

        def mock_response_func(state):
            return {**state, "response": "Test response"}

        mock_generate_response.return_value = mock_response_func

        # Test with specific client, tts, and logger mocks
        specific_client = Mock()
        specific_tts = Mock()
        specific_logger = Mock()

        graph = build_neutral_flow(specific_client, specific_tts, specific_logger)

        mock_generate_response.assert_called_once_with(
            "neutral and friendly", specific_client, specific_tts, specific_logger
        )

    @patch('src.miramind.llm.langgraph.subgraphs.generate_response')
    def test_sad_flow_chat_history_extension(self, mock_generate_response):
        """Test that sad flow properly extends chat history."""

        def mock_response_func(state):
            return {
                **state,
                "response": "I understand.",
                "chat_history": state.get("chat_history", [])
                + [
                    {"role": "user", "content": state["user_input"]},
                    {"role": "assistant", "content": "I understand."},
                ],
            }

        mock_generate_response.return_value = mock_response_func

        initial_state = {
            "user_input": "I'm feeling down",
            "chat_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

        graph = build_sad_flow(self.mock_client, self.mock_tts_provider, self.mock_emotion_logger)
        compiled_graph = graph.compile()

        result = compiled_graph.invoke(initial_state)

        # Should have original history + user input + assistant response + follow-up
        assert len(result["chat_history"]) >= 4

        # Check that follow-up was added as a separate message
        followup_messages = [
            msg
            for msg in result["chat_history"]
            if "Would you like to tell me more" in msg.get("content", "")
        ]
        assert len(followup_messages) == 1
        assert followup_messages[0]["role"] == "assistant"
