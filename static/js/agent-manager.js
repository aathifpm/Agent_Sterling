class AgentManager {
    constructor() {
        // Get backend URL from current domain
        const currentDomain = window.location.hostname;
        this.backendUrl = currentDomain.includes('onrender.com') 
            ? `https://agent-sterling-backend.onrender.com`
            : 'http://localhost:8000';
            
        this.isRunning = false;
        this.statusCheckInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.logs = [];
        
        // Initialize UI elements
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusLog = document.getElementById('statusLog');
        this.activeTime = document.getElementById('activeTime');
        this.postsProcessed = document.getElementById('postsProcessed');
        this.responsesSent = document.getElementById('responsesSent');
        
        // Bind event listeners
        this.startBtn.addEventListener('click', () => this.startAgent());
        this.stopBtn.addEventListener('click', () => this.stopAgent());
        
        // Load saved logs
        this.loadSavedLogs();
        
        // Check if agent was running before page reload
        this.checkAgentStatus();
        
        // Save credentials to localStorage if provided
        this.setupCredentialsPersistence();
    }
    
    setupCredentialsPersistence() {
        // Load saved credentials
        const savedCredentials = localStorage.getItem('agentCredentials');
        if (savedCredentials) {
            const credentials = JSON.parse(savedCredentials);
            document.getElementById('mastodonInstance').value = credentials.instance_url || '';
            document.getElementById('mastodonClientId').value = credentials.client_id || '';
            document.getElementById('mastodonClientSecret').value = credentials.client_secret || '';
            document.getElementById('mastodonToken').value = credentials.access_token || '';
            document.getElementById('geminiApiKey').value = credentials.gemini_api_key || '';
        }
        
        // Save credentials when start button is clicked
        this.startBtn.addEventListener('click', () => {
            const credentials = {
                instance_url: document.getElementById('mastodonInstance').value,
                client_id: document.getElementById('mastodonClientId').value,
                client_secret: document.getElementById('mastodonClientSecret').value,
                access_token: document.getElementById('mastodonToken').value,
                gemini_api_key: document.getElementById('geminiApiKey').value
            };
            localStorage.setItem('agentCredentials', JSON.stringify(credentials));
        });
    }
    
    async loadSavedLogs() {
        try {
            const savedLogs = localStorage.getItem('agentLogs');
            if (savedLogs) {
                this.logs = JSON.parse(savedLogs);
                this.updateLogDisplay();
            }
        } catch (error) {
            console.error('Error loading saved logs:', error);
        }
    }
    
    saveLogs() {
        try {
            localStorage.setItem('agentLogs', JSON.stringify(this.logs));
        } catch (error) {
            console.error('Error saving logs:', error);
        }
    }
    
    async checkAgentStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/api/status`);
            const data = await response.json();
            
            if (data.status === 'running') {
                this.isRunning = true;
                this.startStatusChecks();
                this.updateUIState(true);
            }
            
            // Update logs
            if (data.logs && data.logs.length > 0) {
                this.logs = [...this.logs, ...data.logs];
                this.updateLogDisplay();
                this.saveLogs();
            }
        } catch (error) {
            console.error('Error checking agent status:', error);
        }
    }
    
    async startAgent() {
        try {
            const config = this.getAgentConfig();
            const response = await fetch(`${this.backendUrl}/api/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                this.isRunning = true;
                this.startStatusChecks();
                this.updateUIState(true);
                this.addLog('Agent started successfully', 'success');
            }
        } catch (error) {
            console.error('Error starting agent:', error);
            this.addLog('Failed to start agent: ' + error.message, 'error');
        }
    }
    
    async stopAgent() {
        try {
            const response = await fetch(`${this.backendUrl}/api/stop`, {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.status === 'success') {
                this.isRunning = false;
                this.stopStatusChecks();
                this.updateUIState(false);
                this.addLog('Agent stopped successfully', 'success');
            }
        } catch (error) {
            console.error('Error stopping agent:', error);
            this.addLog('Failed to stop agent: ' + error.message, 'error');
        }
    }
    
    startStatusChecks() {
        if (!this.statusCheckInterval) {
            this.statusCheckInterval = setInterval(() => this.checkStatus(), 5000);
        }
    }
    
    stopStatusChecks() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }
    
    async checkStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/api/status`);
            const data = await response.json();
            
            this.updateMetrics(data);
            
            if (data.logs && data.logs.length > 0) {
                this.logs = [...this.logs, ...data.logs];
                this.updateLogDisplay();
                this.saveLogs();
            }
            
            this.reconnectAttempts = 0;
        } catch (error) {
            console.error('Error checking status:', error);
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                this.stopStatusChecks();
                this.updateUIState(false);
                this.addLog('Lost connection to agent', 'error');
            }
        }
    }
    
    updateUIState(isRunning) {
        this.startBtn.disabled = isRunning;
        this.stopBtn.disabled = !isRunning;
        this.statusIndicator.className = `status-indicator ${isRunning ? 'running' : 'stopped'}`;
        this.statusIndicator.querySelector('.status-text').textContent = isRunning ? 'Running' : 'Stopped';
    }
    
    updateMetrics(data) {
        if (data.posts_processed !== undefined) {
            this.postsProcessed.textContent = data.posts_processed;
        }
        if (data.responses_sent !== undefined) {
            this.responsesSent.textContent = data.responses_sent;
        }
    }
    
    addLog(message, type = 'info') {
        const log = {
            timestamp: new Date().toISOString(),
            type,
            message
        };
        
        this.logs.push(log);
        this.updateLogDisplay();
        this.saveLogs();
    }
    
    updateLogDisplay() {
        const logHtml = this.logs
            .slice(-100) // Keep only last 100 logs in display
            .map(log => `
                <div class="log-entry ${log.type}">
                    <span class="timestamp">${new Date(log.timestamp).toLocaleTimeString()}</span>
                    <span class="message">${log.message}</span>
                </div>
            `)
            .join('');
        
        this.statusLog.innerHTML = logHtml;
        this.statusLog.scrollTop = this.statusLog.scrollHeight;
    }
    
    getAgentConfig() {
        // Get all configuration values from form inputs
        return {
            platform: document.querySelector('.platform-btn.active').dataset.platform,
            credentials: {
                instance_url: document.getElementById('mastodonInstance').value,
                client_id: document.getElementById('mastodonClientId').value,
                client_secret: document.getElementById('mastodonClientSecret').value,
                access_token: document.getElementById('mastodonToken').value,
                gemini_api_key: document.getElementById('geminiApiKey').value
            },
            monitoring: {
                accountToWatch: document.getElementById('accountToWatch').value,
                hashtags: document.getElementById('hashtags').value.split(',').map(h => h.trim()),
                checkInterval: parseInt(document.getElementById('checkInterval').value)
            },
            response: {
                type: document.getElementById('responseType').value,
                useEmojis: document.getElementById('useEmojis').checked,
                maxLength: parseInt(document.getElementById('maxResponseLength').value)
            },
            rateLimits: {
                maxPostsPerHour: parseInt(document.getElementById('maxPostsPerHour').value),
                cooldownPeriod: parseInt(document.getElementById('cooldownPeriod').value)
            },
            filters: {
                keywords: document.getElementById('keywords').value.split(',').map(k => k.trim()),
                blacklist: document.getElementById('blacklist').value.split(',').map(b => b.trim())
            },
            postStyle: {
                style: document.getElementById('postStyle').value,
                postStyleEmojis: document.getElementById('postStyleEmojis').checked,
                useHashtags: document.getElementById('useHashtags').checked,
                maxLength: parseInt(document.getElementById('postStyleMaxLength').value)
            },
            dm_settings: {
                enabled: document.getElementById('dmEnabled').checked,
                auto_reply: document.getElementById('autoReply').checked,
                reply_interval: parseInt(document.getElementById('replyInterval').value)
            },
            like_settings: {
                enabled: document.getElementById('likeEnabled').checked,
                max_likes_per_hour: parseInt(document.getElementById('maxLikesPerHour').value),
                like_probability: parseInt(document.getElementById('likeProbability').value) / 100
            },
            auto_post_settings: {
                enabled: document.getElementById('autoPostEnabled').checked,
                interval: parseInt(document.getElementById('postInterval').value),
                max_daily_posts: parseInt(document.getElementById('maxDailyPosts').value)
            }
        };
    }
}

// Initialize the agent manager when the page loads
window.addEventListener('DOMContentLoaded', () => {
    window.agentManager = new AgentManager();
}); 