# QA Thoughts CLI Tools

A set of command-line tools for recording questions, answers, and thoughts with automatic timestamping and unique identifiers.

## Features

- Record questions, answers, and random thoughts from the command line
- Automatic timestamping in ISO 8601 format
- Unique UUID generation for each entry
- User association with system username
- CSV storage with proper escaping of special characters
- Support for linking answers to specific questions

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installing from Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/qa_thoughts.git
cd qa_thoughts
```

2. Install the package:
```bash
pip install .
```

This will install three command-line tools: `question`, `answer`, and `thought`.

## Usage

### Recording a Question

```bash
question "What is the meaning of life?"
```

The command will output a UUID for the question, which you can use when providing an answer:
```
Question recorded with UUID: 123e4567-e89b-12d3-a456-426614174000
```

### Recording an Answer

To answer a specific question:
```bash
answer -q 123e4567-e89b-12d3-a456-426614174000 "The meaning of life is 42."
```

To record a standalone answer/fact:
```bash
answer "The speed of light is approximately 299,792,458 meters per second."
```

### Recording a Thought

```bash
thought "I should learn more about quantum computing."
```

### Storage Location

All entries are stored in CSV files under `~/.qa_thoughts/`:
- Questions: `~/.qa_thoughts/questions/questions.csv`
- Answers: `~/.qa_thoughts/answers/answers.csv`
- Thoughts: `~/.qa_thoughts/thoughts/thoughts.csv`

### CSV File Format

#### Questions
```csv
uuid,timestamp,username,content
123e4567-e89b-12d3-a456-426614174000,2024-03-19T15:30:00,alice,"What is the meaning of life?"
```

#### Answers
```csv
uuid,question_uuid,timestamp,username,content
123e4567-e89b-12d3-a456-426614174001,123e4567-e89b-12d3-a456-426614174000,2024-03-19T15:35:00,bob,"The meaning of life is 42."
```

#### Thoughts
```csv
uuid,timestamp,username,content
123e4567-e89b-12d3-a456-426614174002,2024-03-19T16:00:00,carol,"I should learn more about quantum computing."
```

## Error Handling

### Invalid UUID Format
When providing a question UUID for an answer, if the UUID format is invalid:
```bash
$ answer -q invalid-uuid "This won't work"
Error: Invalid question UUID format
```

### General Errors
The tools will provide appropriate error messages for common issues:
- File permission errors
- Invalid input formatting
- Storage directory access problems

## Development

### Project Structure
```
qa_thoughts/
├── src/
│   └── qa_thoughts/
│       ├── commands/       # Command handlers
│       ├── models/         # Data models
│       └── utils/          # Utility functions
└── tests/                  # Test suite
```

### Running Tests
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## License

[Your chosen license] 