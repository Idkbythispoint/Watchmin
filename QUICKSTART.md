# Watchmin - Quick Start Guide

## Installation

```bash
pip install -r requirements.txt
```

## Basic Usage

### 1. Get Help (No API Key Required)
```bash
python main.py --help
```

### 2. Monitor a New Process
```bash
python main.py --watch_process "python your_script.py"
```

### 3. Attach to Existing Process
```bash
python main.py --attach <PID>
```

### 4. List Active Watchers
```bash
python main.py --list
```

### 5. Stop a Watcher
```bash
python main.py --stop <watcher_id>
```

## API Key Setup

The application will prompt for your OpenAI API key when repair functionality is needed. You can also:

1. Set environment variable: `export OPENAI_API_KEY=your_key_here`
2. Create `openai.key` file with your API key

## Testing

Run the demonstration test:
```bash
python simple_watchmin_test.py
```

Run the full test suite:
```bash
python run_full_test.py
```
