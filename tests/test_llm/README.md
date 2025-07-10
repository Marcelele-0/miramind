# LLM/LangGraph Test Suite

This directory contains comprehensive tests for the MiraMind LLM/LangGraph chatbot system. The test suite covers all major components and provides integration testing for the complete emotion-based conversation flow.

## Test Structure

```
test_llm/
├── conftest.py                 # Pytest configuration and shared fixtures
├── test_chatbot.py            # Tests for main chatbot functionality
├── test_utils.py              # Tests for utility functions
├── test_subgraphs.py          # Tests for emotion-specific subgraphs
├── test_performance_monitor.py # Tests for performance monitoring
├── test_performance_config.py  # Tests for configuration constants
├── test_run_chat.py           # Tests for chat processing pipeline
├── test_integration.py        # Integration tests for complete flows
└── README.md                  # This file
```

## Test Categories

### Unit Tests (Default)

- **test_chatbot.py**: Core chatbot functionality, emotion detection, graph construction
- **test_utils.py**: Utility functions like EmotionLogger, OpenAI API calls, response generation
- **test_subgraphs.py**: Individual emotion flow testing (sad, happy, angry, etc.)
- **test_performance_monitor.py**: Performance tracking and metrics
- **test_performance_config.py**: Configuration validation
- **test_run_chat.py**: Chat processing pipeline, caching, audio handling

### Integration Tests

- **test_integration.py**: End-to-end testing of complete conversation flows

## Running Tests

### Basic Test Run

```bash
# Run all tests
pytest tests/test_llm/

# Run specific test file
pytest tests/test_llm/test_chatbot.py

# Run with verbose output
pytest tests/test_llm/ -v
```

### Test Categories

```bash
# Run only unit tests
pytest tests/test_llm/ -m unit

# Run integration tests
pytest tests/test_llm/ -m integration --run-integration

# Run performance tests
pytest tests/test_llm/ -m performance --run-performance

# Run slow tests
pytest tests/test_llm/ -m slow --run-slow
```

### Coverage Report

```bash
# Generate coverage report
pytest tests/test_llm/ --cov=src.miramind.llm.langgraph --cov-report=html

# Generate coverage with missing lines
pytest tests/test_llm/ --cov=src.miramind.llm.langgraph --cov-report=term-missing
```

## Test Components

### Chatbot Tests (`test_chatbot.py`)

- **EmotionResult model validation**: Tests Pydantic model for emotion results
- **Emotion detection**: Tests emotion parsing from OpenAI responses
- **Graph construction**: Tests LangGraph setup and routing
- **Client initialization**: Tests OpenAI and TTS client setup
- **Error handling**: Tests fallback behavior for invalid responses

### Utils Tests (`test_utils.py`)

- **EmotionLogger**: Tests logging functionality and file I/O
- **OpenAI API calls**: Tests sync and async API interactions
- **Response generation**: Tests emotion-specific response creation
- **TTS integration**: Tests text-to-speech synthesis
- **Error handling**: Tests API failure scenarios

### Subgraphs Tests (`test_subgraphs.py`)

- **Flow construction**: Tests creation of emotion-specific flows
- **Response styles**: Tests appropriate response styles for each emotion
- **State preservation**: Tests that flows maintain conversation state
- **Follow-up logic**: Tests sad flow's additional follow-up questions

### Performance Monitor Tests (`test_performance_monitor.py`)

- **Operation tracking**: Tests timing and memory usage tracking
- **Statistics calculation**: Tests metrics aggregation and reporting
- **Thread safety**: Tests concurrent operation tracking
- **Context managers**: Tests track_operation context manager

### Run Chat Tests (`test_run_chat.py`)

- **Message processing**: Tests complete chat message pipeline
- **Caching**: Tests response caching functionality
- **Audio handling**: Tests audio file saving and error handling
- **Performance monitoring**: Tests integration with performance tracking

### Integration Tests (`test_integration.py`)

- **End-to-end flows**: Tests complete conversation flows for different emotions
- **State management**: Tests conversation state across multiple interactions
- **Error scenarios**: Tests system behavior during component failures
- **Performance integration**: Tests performance monitoring in complete flows

## Test Fixtures

### Shared Fixtures (conftest.py)

- **mock_openai_client**: Mock OpenAI client for testing
- **mock_tts_provider**: Mock TTS provider for testing
- **mock_emotion_logger**: Mock emotion logger for testing
- **sample_chat_state**: Sample conversation state for testing
- **sample_emotion_states**: Pre-configured states for different emotions
- **mock_environment_vars**: Mock environment variables for testing

## Mocking Strategy

The tests use extensive mocking to isolate components and avoid external dependencies:

1. **OpenAI API**: Mocked to avoid API calls and costs
2. **TTS Provider**: Mocked to avoid audio processing dependencies
3. **File I/O**: Mocked for audio saving and logging
4. **Environment Variables**: Mocked for configuration testing
5. **Performance Monitoring**: Mocked for testing without side effects

## Test Data

### Sample Inputs

- Various emotional expressions ("I'm happy!", "I'm sad", "I'm angry")
- Edge cases (empty input, unicode characters, malformed JSON)
- Different conversation contexts (new chat, existing history, memory)

### Expected Outputs

- Proper emotion classification (happy, sad, angry, neutral, etc.)
- Appropriate response styles for each emotion
- Valid conversation state management
- Audio generation and saving
- Performance metrics collection

## Performance Testing

The test suite includes performance-related tests that verify:

- Response time tracking
- Memory usage monitoring
- Cache effectiveness
- Threading safety
- Resource cleanup

## Error Handling Tests

Comprehensive error handling tests cover:

- OpenAI API failures
- TTS synthesis errors
- File I/O errors
- Invalid JSON responses
- Network timeouts
- Invalid emotion classifications

## Configuration Testing

Configuration tests ensure:

- All required constants are defined
- Values are within reasonable ranges
- Boolean flags are properly typed
- Model names follow expected formats
- Timeout values are appropriate

## Best Practices

1. **Test Isolation**: Each test is independent and doesn't rely on others
2. **Mock External Dependencies**: No real API calls or file operations
3. **Clear Test Names**: Test names describe what they're testing
4. **Comprehensive Coverage**: Tests cover both success and failure scenarios
5. **Performance Awareness**: Tests don't create unnecessary overhead
6. **Documentation**: Each test class and method is documented

## Running in CI/CD

The test suite is designed to run in CI/CD environments:

- No external dependencies required
- Fast execution time for unit tests
- Separate markers for different test types
- Configurable test selection
- Coverage reporting support

## Debugging Tests

For debugging failing tests:

```bash
# Run with extra verbose output
pytest tests/test_llm/ -vvv

# Run specific test with debugging
pytest tests/test_llm/test_chatbot.py::TestChatbot::test_detect_emotion_valid_response -s

# Run with pdb debugger
pytest tests/test_llm/ --pdb

# Run with coverage to see what's not tested
pytest tests/test_llm/ --cov=src.miramind.llm.langgraph --cov-report=html
```

## Adding New Tests

When adding new functionality to the LLM system:

1. **Add unit tests** for the new component
2. **Update integration tests** if the change affects the complete flow
3. **Add performance tests** if the change impacts performance
4. **Update fixtures** if new test data is needed
5. **Document the tests** with clear descriptions

## Test Maintenance

- **Regular updates**: Keep tests updated with code changes
- **Performance monitoring**: Watch for test execution time increases
- **Coverage tracking**: Maintain high test coverage
- **Dependency management**: Keep test dependencies minimal
- **Documentation**: Keep test documentation current
