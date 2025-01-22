const express = require('express');
const app = express();
const port = 3001;

app.get('/', (req, res) => {
    res.send('Test server is running!');
});

app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Test server running at http://localhost:${port}`);
    console.log(`Try accessing:
    1. http://localhost:${port}
    2. http://127.0.0.1:${port}
    3. http://0.0.0.0:${port}`);
});
