# Poe Canvas Communication - Debugging Notes

## Current Setup

### Canvas App Sends:
```javascript
window.parent.postMessage({
    type: 'sendMessage',
    message: JSON.stringify({
        type: 'birth_data',
        date: '1990-03-15',
        time: '14:30',
        city: 'Austin, TX'
    }),
}, '*');
```

### Canvas App Expects:
```javascript
window.addEventListener('message', (event) => {
    const { type, data } = event.data;
    if (type === 'botResponse') {
        handleBotChunk(data.text);  // ← Never receives this
    }
});
```

### Bot Currently Does:
```python
yield fp.PartialResponse(text=chart_json + "\n---\n")
async for chunk in self.get_interpretation(chart, request):
    yield chunk
```

## The Problem

The bot's response (`fp.PartialResponse`) goes to the **main Poe chat**, not directly to the Canvas app via `postMessage`.

The Canvas app is waiting for a message with `type: 'botResponse'` but Poe never sends messages in that format to child windows.

## How Poe Canvas Actually Works

Poe Canvas apps work differently:

1. User submits data in Canvas → sends via `postMessage` to Poe
2. Poe forwards data to bot as user query
3. Bot responds → response displayed in main chat
4. **Canvas app can read the bot's response from the DOM or message context**

## Fix Options

### Option 1: Read Response from Message DOM (Recommended)

Instead of waiting for `postMessage` events, read the bot's response from the displayed message:

```javascript
// After sending data, poll for the bot's response
const checkForResponse = setInterval(() => {
    const messages = document.querySelectorAll('.message-content');
    const lastMessage = messages[messages.length - 1];
    if (lastMessage && lastMessage.textContent.includes('chart_result')) {
        clearInterval(checkForResponse);
        const chartData = extractChartData(lastMessage.textContent);
        renderChartWheel(chartData);
    }
}, 500);
```

### Option 2: Use Poe's Canvas-Specific Messaging (if available)

Check if fastapi_poe has Canvas-specific response types. If not, Option 1 is the way.

### Option 3: Simplified Approach

Skip Canvas for now, have the bot respond in main chat with:
1. Chart data summary (text)
2. Interpretation (streamed)

Then add Canvas later if needed.

## Next Steps

1. Test if Poe provides the bot's response to Canvas app in any way
2. If not, implement DOM polling (Option 1)
3. Or simplify to main chat only (Option 3)
