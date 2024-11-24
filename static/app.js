class AgentController {
    constructor() {
        this.config = {
            platform: 'mastodon',
            monitoring: {
                accountToWatch: '',
                hashtags: [],
                checkInterval: 60
            },
            response: {
                type: 'entertainment',
                useEmojis: true,
                maxLength: 240
            },
            rateLimits: {
                maxPostsPerHour: 10,
                cooldownPeriod: 5
            },
            filters: {
                keywords: [],
                blacklist: []
            }
        };

        this.isRunning = false;
        this.startTime = null;
        this.statusCheckInterval = null;
        this.metrics = {
            postsProcessed: 0,
            responsesSent: 0
        };
        
        this.baseUrl = 'http://localhost:8000/api';
        this.initializeEventListeners();
        this.loadConfiguration();
        this.updateMetricsDisplay();
    }

    initializeEventListeners() {
        // Platform toggle
        document.querySelectorAll('.platform-btn').forEach(btn => {
            btn.addEventListener('click', () => this.togglePlatform(btn.dataset.platform));
        });

        // Button event listeners
        document.getElementById('startBtn').addEventListener('click', async () => {
            if (!this.isRunning) {
                await this.startAgent();
            }
        });
        document.getElementById('stopBtn').addEventListener('click', async () => {
            if (this.isRunning) {
                await this.stopAgent();
            }
        });
        document.getElementById('saveConfig').addEventListener('click', () => this.saveConfiguration());

        // Mastodon settings
        document.getElementById('mastodonInstance').addEventListener('input', (e) => {
            this.config.credentials.mastodon.instance_url = e.target.value;
        });
        document.getElementById('mastodonClientId').addEventListener('input', (e) => {
            this.config.credentials.mastodon.client_id = e.target.value;
        });
        document.getElementById('mastodonClientSecret').addEventListener('input', (e) => {
            this.config.credentials.mastodon.client_secret = e.target.value;
        });
        document.getElementById('mastodonToken').addEventListener('input', (e) => {
            this.config.credentials.mastodon.access_token = e.target.value;
        });

        // Twitter settings
        document.getElementById('twitterApiKey').addEventListener('input', (e) => {
            this.config.credentials.twitter.api_key = e.target.value;
        });
        document.getElementById('twitterApiSecret').addEventListener('input', (e) => {
            this.config.credentials.twitter.api_secret = e.target.value;
        });
        document.getElementById('twitterAccessToken').addEventListener('input', (e) => {
            this.config.credentials.twitter.access_token = e.target.value;
        });
        document.getElementById('twitterAccessSecret').addEventListener('input', (e) => {
            this.config.credentials.twitter.access_token_secret = e.target.value;
        });
        document.getElementById('twitterBearerToken').addEventListener('input', (e) => {
            this.config.credentials.twitter.bearer_token = e.target.value;
        });

        // Monitoring settings
        document.getElementById('accountToWatch').addEventListener('input', (e) => {
            this.config.monitoring.accountToWatch = e.target.value;
        });
        document.getElementById('hashtags').addEventListener('input', (e) => {
            const hashtagsStr = e.target.value;
            this.config.monitoring.hashtags = hashtagsStr
                .split(',')
                .map(tag => tag.trim())
                .filter(tag => tag) // Remove empty tags
                .map(tag => tag.startsWith('#') ? tag.substring(1) : tag); // Remove # if present
        });
        document.getElementById('checkInterval').addEventListener('input', (e) => {
            this.config.monitoring.checkInterval = parseInt(e.target.value);
        });

        // Response settings
        document.getElementById('responseType').addEventListener('change', (e) => {
            this.config.response.type = e.target.value;
        });
        document.getElementById('useEmojis').addEventListener('change', (e) => {
            this.config.response.useEmojis = e.target.checked;
        });
        document.getElementById('maxResponseLength').addEventListener('input', (e) => {
            this.config.response.maxLength = parseInt(e.target.value);
        });

        // Rate limits
        document.getElementById('maxPostsPerHour').addEventListener('input', (e) => {
            this.config.rateLimits.maxPostsPerHour = parseInt(e.target.value);
        });
        document.getElementById('cooldownPeriod').addEventListener('input', (e) => {
            this.config.rateLimits.cooldownPeriod = parseInt(e.target.value);
        });

        // Content filters
        document.getElementById('keywords').addEventListener('input', (e) => {
            this.config.filters.keywords = e.target.value.split(',').map(k => k.trim());
        });
        document.getElementById('blacklist').addEventListener('input', (e) => {
            this.config.filters.blacklist = e.target.value.split(',').map(b => b.trim());
        });
    }

    togglePlatform(platform) {
        this.config.platform = platform;
        document.querySelectorAll('.platform-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.platform === platform);
        });
        document.getElementById('mastodon-config').style.display = platform === 'mastodon' ? 'block' : 'none';
        document.getElementById('twitter-config').style.display = platform === 'twitter' ? 'block' : 'none';
    }

    async startAgent() {
        try {
            // Validate configuration
            if (!this.validateConfig()) {
                this.log('error', 'Please configure hashtags to monitor and check interval');
                return;
            }

            // Prepare config
            const configToSend = {
                ...this.config,
                monitoring: {
                    ...this.config.monitoring,
                    hashtags: Array.isArray(this.config.monitoring.hashtags) 
                        ? this.config.monitoring.hashtags 
                        : this.config.monitoring.hashtags.split(',')
                            .map(h => h.trim())
                            .filter(h => h)
                            .map(h => h.startsWith('#') ? h.substring(1) : h),
                    checkInterval: parseInt(this.config.monitoring.checkInterval)
                }
            };

            console.log('Sending config:', configToSend); // Debug log

            const response = await fetch(`${this.baseUrl}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(configToSend)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to start agent');
            }

            const data = await response.json();
            this.isRunning = true;
            this.startTime = new Date();
            this.updateUIState(true);
            
            // Start status checking
            this.startStatusChecking();
            
            this.log('success', 'Agent started successfully');
            
        } catch (error) {
            this.log('error', `Failed to start agent: ${error.message}`);
            console.error('Error details:', error); // Debug log
            this.updateUIState(false);
        }
    }

    async stopAgent() {
        try {
            const response = await fetch(`${this.baseUrl}/stop`, {
                method: 'POST'
            });

            if (!response.ok) {
                throw new Error('Failed to stop agent');
            }

            this.isRunning = false;
            this.updateUIState(false);
            
            // Stop status checking
            this.stopStatusChecking();
            
            this.log('success', 'Agent stopped successfully');
            
        } catch (error) {
            this.log('error', `Failed to stop agent: ${error.message}`);
        }
    }

    saveConfiguration() {
        // Warn about storing sensitive data
        if (confirm('Warning: Saving configuration will store your API keys locally. Continue?')) {
            localStorage.setItem('agentConfig', JSON.stringify(this.config));
            this.log('success', 'Configuration saved successfully');
        } else {
            this.log('warning', 'Configuration save cancelled');
        }
    }

    loadConfiguration() {
        const savedConfig = localStorage.getItem('agentConfig');
        if (savedConfig) {
            try {
                this.config = JSON.parse(savedConfig);
                this.updateUIFromConfig();
                this.log('success', 'Configuration loaded successfully');
            } catch (error) {
                this.log('error', 'Failed to load configuration');
                localStorage.removeItem('agentConfig');
            }
        }
    }

    updateUIFromConfig() {
        // Platform
        this.togglePlatform(this.config.platform);

        // Mastodon settings
        document.getElementById('mastodonInstance').value = this.config.credentials.mastodon.instance_url;
        document.getElementById('mastodonClientId').value = this.config.credentials.mastodon.client_id;
        document.getElementById('mastodonClientSecret').value = this.config.credentials.mastodon.client_secret;
        document.getElementById('mastodonToken').value = this.config.credentials.mastodon.access_token;

        // Twitter settings
        document.getElementById('twitterApiKey').value = this.config.credentials.twitter.api_key;
        document.getElementById('twitterApiSecret').value = this.config.credentials.twitter.api_secret;
        document.getElementById('twitterAccessToken').value = this.config.credentials.twitter.access_token;
        document.getElementById('twitterAccessSecret').value = this.config.credentials.twitter.access_token_secret;
        document.getElementById('twitterBearerToken').value = this.config.credentials.twitter.bearer_token;

        // Monitoring settings
        document.getElementById('accountToWatch').value = this.config.monitoring.accountToWatch;
        document.getElementById('hashtags').value = Array.isArray(this.config.monitoring.hashtags)
            ? this.config.monitoring.hashtags.map(h => `#${h}`).join(', ')
            : this.config.monitoring.hashtags;
        document.getElementById('checkInterval').value = this.config.monitoring.checkInterval;

        // Response settings
        document.getElementById('responseType').value = this.config.response.type;
        document.getElementById('useEmojis').checked = this.config.response.useEmojis;
        document.getElementById('maxResponseLength').value = this.config.response.maxLength;

        // Rate limits
        document.getElementById('maxPostsPerHour').value = this.config.rateLimits.maxPostsPerHour;
        document.getElementById('cooldownPeriod').value = this.config.rateLimits.cooldownPeriod;

        // Content filters
        document.getElementById('keywords').value = this.config.filters.keywords.join(', ');
        document.getElementById('blacklist').value = this.config.filters.blacklist.join(', ');
    }

    updateMetricsDisplay() {
        if (this.startTime) {
            const now = new Date();
            const diff = now - this.startTime;
            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            
            // Animate the numbers
            this.animateValue('activeTime', 
                `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`);
        }

        this.animateValue('postsProcessed', this.metrics.postsProcessed);
        this.animateValue('responsesSent', this.metrics.responsesSent);
    }

    animateValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.transition = 'all 0.3s ease';
            element.textContent = value;
            element.style.transform = 'scale(1.1)';
            setTimeout(() => {
                element.style.transform = 'scale(1)';
            }, 300);
        }
    }

    startStatusChecking() {
        if (!this.statusCheckInterval) {
            this.statusCheckInterval = setInterval(() => this.checkStatus(), 1000);
        }
    }

    stopStatusChecking() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
            this.statusCheckInterval = null;
        }
    }

    async checkStatus() {
        try {
            const response = await fetch(`${this.baseUrl}/status`);
            const data = await response.json();
            
            // Update metrics
            this.metrics.postsProcessed = data.posts_processed;
            this.metrics.responsesSent = data.responses_sent;
            
            // Process new logs
            if (data.logs && data.logs.length > 0) {
                data.logs.forEach(log => this.log(log.type, log.message, log.details));
            }
            
            this.updateMetricsDisplay();
            
            // Check if agent stopped unexpectedly
            if (!data.status === 'running' && this.isRunning) {
                this.isRunning = false;
                this.updateUIState(false);
                this.log('error', 'Agent stopped unexpectedly');
            }
            
        } catch (error) {
            this.log('error', `Error checking status: ${error.message}`);
        }
    }

    updateUIState(running) {
        // Update button states
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        startBtn.disabled = running;
        stopBtn.disabled = !running;
        
        // Update status indicator
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = statusIndicator.querySelector('.status-text');
        
        statusIndicator.className = `status-indicator ${running ? 'running' : 'stopped'}`;
        statusText.textContent = running ? 'Running' : 'Stopped';
        
        // Toggle config inputs
        this.toggleConfigInputs(running);
    }

    log(type, message, details = null) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        // Create timestamp
        const timestamp = new Date().toLocaleTimeString();
        
        // Create main message
        const messageText = document.createElement('div');
        messageText.className = 'log-message';
        messageText.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        logEntry.appendChild(messageText);
        
        // Add details if provided
        if (details) {
            const detailsText = document.createElement('div');
            detailsText.className = 'log-details';
            if (typeof details === 'object') {
                // Pretty print objects
                detailsText.innerHTML = Object.entries(details)
                    .map(([key, value]) => `<span class="log-key">${key}:</span> ${value}`)
                    .join('<br>');
            } else {
                detailsText.textContent = details;
            }
            logEntry.appendChild(detailsText);
        }
        
        const statusLog = document.getElementById('statusLog');
        
        // Add with animation
        logEntry.style.opacity = '0';
        logEntry.style.transform = 'translateY(10px)';
        statusLog.appendChild(logEntry);
        
        // Trigger animation
        requestAnimationFrame(() => {
            logEntry.style.transition = 'all 0.3s ease';
            logEntry.style.opacity = '1';
            logEntry.style.transform = 'translateY(0)';
        });
        
        // Scroll to bottom
        statusLog.scrollTop = statusLog.scrollHeight;
        
        // Keep only last 100 entries
        while (statusLog.children.length > 100) {
            statusLog.removeChild(statusLog.firstChild);
        }
    }

    validateCredentials() {
        const platform = this.config.platform;
        const creds = this.config.credentials[platform];
        
        return Object.values(creds).every(value => value && value.trim() !== '');
    }

    validateConfig() {
        // Check if hashtags are configured
        const hashtags = this.config.monitoring.hashtags;
        if (!hashtags || 
            (Array.isArray(hashtags) && hashtags.length === 0) || 
            (typeof hashtags === 'string' && !hashtags.trim())) {
            this.log('error', 'Please enter at least one hashtag to monitor');
            return false;
        }

        // Check if interval is valid
        const interval = parseInt(this.config.monitoring.checkInterval);
        if (isNaN(interval) || interval < 30) {
            this.log('error', 'Check interval must be at least 30 seconds');
            return false;
        }

        return true;
    }

    toggleConfigInputs(disabled) {
        // Disable/enable configuration inputs while agent is running
        const inputs = [
            'hashtags',
            'checkInterval',
            'responseType',
            'useEmojis',
            'maxResponseLength',
            'maxPostsPerHour',
            'cooldownPeriod',
            'keywords',
            'blacklist'
        ];

        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.disabled = disabled;
            }
        });
    }

    resetUI() {
        // Reset UI to initial state
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('startBtn').classList.remove('disabled');
        document.getElementById('stopBtn').classList.add('disabled');
        this.toggleConfigInputs(false);
    }

    updateStatus() {
        const indicator = document.getElementById('statusIndicator');
        const statusText = indicator.querySelector('.status-text');
        
        if (this.isRunning) {
            indicator.className = 'status-indicator running';
            statusText.textContent = 'Running';
        } else {
            indicator.className = 'status-indicator stopped';
            statusText.textContent = 'Stopped';
        }
    }
}

// Initialize the controller when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.agentController = new AgentController();
}); 