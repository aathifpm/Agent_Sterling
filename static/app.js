    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        let container = document.querySelector('.notification-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notification-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    class AgentController {
        constructor() {
            // Get backend URL based on environment
            const currentDomain = window.location.hostname;
            this.baseUrl = currentDomain.includes('onrender.com')
                ? `https://${currentDomain.replace('agent-sterling-frontend', 'agent-sterling-backend')}/api`
                : 'http://localhost:8000/api';

            this.config = {
                platform: 'mastodon',
                credentials: {
                    instance_url: '',
                    client_id: '',
                    client_secret: '',
                    access_token: '',
                    gemini_api_key: '',
                    twitter: {
                        api_key: '',
                        api_secret: '',
                        access_token: '',
                        access_token_secret: '',
                        bearer_token: ''
                    }
                },
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
                },
                // Add DM settings
                dm_settings: {
                    enabled: false,
                    auto_reply: true,
                    reply_interval: 300
                },
                // Add Like settings
                like_settings: {
                    enabled: false,
                    max_likes_per_hour: 20,
                    like_probability: 0.7
                },
                auto_post_settings: {
                    enabled: true,
                    interval: 1800,
                    max_daily_posts: 48
                }
            };

            this.isRunning = false;
            this.startTime = null;
            this.statusCheckInterval = null;
            this.metrics = {
                postsProcessed: 0,
                responsesSent: 0
            };
            
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
                this.config.credentials.instance_url = e.target.value;
            });
            document.getElementById('mastodonClientId').addEventListener('input', (e) => {
                this.config.credentials.client_id = e.target.value;
            });
            document.getElementById('mastodonClientSecret').addEventListener('input', (e) => {
                this.config.credentials.client_secret = e.target.value;
            });
            document.getElementById('mastodonToken').addEventListener('input', (e) => {
                this.config.credentials.access_token = e.target.value;
            });
            document.getElementById('geminiApiKey').addEventListener('input', (e) => {
                this.config.credentials.gemini_api_key = e.target.value;
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

            // DM Settings
            document.getElementById('dmEnabled').addEventListener('change', () => {
                this.config.dm_settings.enabled = document.getElementById('dmEnabled').checked;
                if (this.isRunning) this.updateDMSettings();
            });

            document.getElementById('autoReply').addEventListener('change', () => {
                this.config.dm_settings.auto_reply = document.getElementById('autoReply').checked;
                if (this.isRunning) this.updateDMSettings();
            });

            document.getElementById('replyInterval').addEventListener('input', () => {
                this.config.dm_settings.reply_interval = parseInt(document.getElementById('replyInterval').value);
                if (this.isRunning) this.updateDMSettings();
            });

            // Like Settings
            document.getElementById('likeEnabled').addEventListener('change', () => {
                this.config.like_settings.enabled = document.getElementById('likeEnabled').checked;
                if (this.isRunning) this.updateLikeSettings();
            });

            document.getElementById('maxLikesPerHour').addEventListener('input', () => {
                this.config.like_settings.max_likes_per_hour = parseInt(document.getElementById('maxLikesPerHour').value);
                if (this.isRunning) this.updateLikeSettings();
            });

            document.getElementById('likeProbability').addEventListener('input', () => {
                this.config.like_settings.like_probability = parseInt(document.getElementById('likeProbability').value) / 100;
                if (this.isRunning) this.updateLikeSettings();
            });

            // Auto-posting settings
            document.getElementById('autoPostEnabled').addEventListener('change', () => {
                this.config.auto_post_settings.enabled = document.getElementById('autoPostEnabled').checked;
                if (this.isRunning) this.updateAutoPostSettings();
            });

            document.getElementById('postInterval').addEventListener('input', () => {
                this.config.auto_post_settings.interval = parseInt(document.getElementById('postInterval').value);
                if (this.isRunning) this.updateAutoPostSettings();
            });

            document.getElementById('maxDailyPosts').addEventListener('input', () => {
                this.config.auto_post_settings.max_daily_posts = parseInt(document.getElementById('maxDailyPosts').value);
                if (this.isRunning) this.updateAutoPostSettings();
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
                // Validate configuration before sending
                if (!this.validateCredentials()) {
                    return;
                }

                if (!this.validateConfig()) {
                    return;
                }

                // Prepare credentials based on platform
                const credentials = this.config.platform === 'mastodon' ? {
                    instance_url: this.config.credentials.instance_url,
                    client_id: this.config.credentials.client_id,
                    client_secret: this.config.credentials.client_secret,
                    access_token: this.config.credentials.access_token,
                    gemini_api_key: this.config.credentials.gemini_api_key
                } : {
                    ...this.config.credentials.twitter
                };

                const config = {
                    platform: this.config.platform,
                    credentials,
                    monitoring: {
                        accountToWatch: this.config.monitoring.accountToWatch,
                        hashtags: this.config.monitoring.hashtags,
                        checkInterval: this.config.monitoring.checkInterval
                    },
                    response: this.config.response,
                    rateLimits: {
                        ...this.config.rateLimits,
                        cooldownPeriod: this.config.rateLimits.cooldownPeriod * 60 // Convert to seconds
                    },
                    filters: this.config.filters,
                    dm_settings: this.config.dm_settings,
                    like_settings: this.config.like_settings,
                    auto_post_settings: this.config.auto_post_settings,
                    postStyle: {
                        style: "entertainer",
                        postStyleEmojis: true,
                        useHashtags: true,
                        maxLength: 240
                    }
                };

                console.log('Config being sent to server:', JSON.stringify(config, null, 2));

                const response = await fetch(`${this.baseUrl}/start`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                
                if (!response.ok) {
                    console.log('Server validation error:', data);
                    let errorMessage;
                    if (data.detail && typeof data.detail === 'object') {
                        // Handle Pydantic validation errors
                        if (Array.isArray(data.detail)) {
                            errorMessage = data.detail.map(err => 
                                `${err.loc.join('.')}: ${err.msg}`
                            ).join('\n');
                        } else {
                            errorMessage = JSON.stringify(data.detail, null, 2);
                        }
                    } else {
                        errorMessage = data.detail || 'Failed to start agent';
                    }
                    this.log('error', `Validation error: ${errorMessage}`);
                    throw new Error(errorMessage);
                }

                this.isRunning = true;
                this.startTime = new Date();
                this.updateUIState(true);
                this.startStatusChecking();
                this.log('success', 'Agent started successfully');
            } catch (error) {
                console.error('Full error object:', error);
                this.log('error', `Error starting agent: ${error.message}`);
                this.isRunning = false;
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
            document.getElementById('mastodonInstance').value = this.config.credentials.instance_url;
            document.getElementById('mastodonClientId').value = this.config.credentials.client_id;
            document.getElementById('mastodonClientSecret').value = this.config.credentials.client_secret;
            document.getElementById('mastodonToken').value = this.config.credentials.access_token;
            document.getElementById('geminiApiKey').value = this.config.credentials.gemini_api_key;

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

            // DM settings
            document.getElementById('dmEnabled').checked = this.config.dm_settings.enabled;
            document.getElementById('autoReply').checked = this.config.dm_settings.auto_reply;
            document.getElementById('replyInterval').value = this.config.dm_settings.reply_interval;

            // Like settings
            document.getElementById('likeEnabled').checked = this.config.like_settings.enabled;
            document.getElementById('maxLikesPerHour').value = this.config.like_settings.max_likes_per_hour;
            document.getElementById('likeProbability').value = this.config.like_settings.like_probability * 100;

            // Auto-posting settings
            document.getElementById('autoPostEnabled').checked = this.config.auto_post_settings.enabled;
            document.getElementById('postInterval').value = this.config.auto_post_settings.interval;
            document.getElementById('maxDailyPosts').value = this.config.auto_post_settings.max_daily_posts;
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
            if (!this.config || !this.config.platform) {
                this.log('error', 'Configuration not initialized properly');
                return false;
            }

            const platform = this.config.platform;
            let isValid = true;
            let requiredFields = [];

            // Define required fields for each platform
            if (platform === 'mastodon') {
                requiredFields = [
                    { id: 'geminiApiKey', label: 'Gemini API Key' },
                    { id: 'mastodonInstance', label: 'Instance URL' },
                    { id: 'mastodonClientId', label: 'Client ID' },
                    { id: 'mastodonClientSecret', label: 'Client Secret' },
                    { id: 'mastodonToken', label: 'Access Token' }
                ];
            } else if (platform === 'twitter') {
                requiredFields = [
                    { id: 'twitterApiKey', label: 'API Key' },
                    { id: 'twitterApiSecret', label: 'API Secret' },
                    { id: 'twitterAccessToken', label: 'Access Token' },
                    { id: 'twitterAccessSecret', label: 'Access Token Secret' },
                    { id: 'twitterBearerToken', label: 'Bearer Token' }
                ];
            } else {
                this.log('error', 'Invalid platform selected');
                return false;
            }

            // Check each required field
            const missingFields = requiredFields.filter(field => {
                const element = document.getElementById(field.id);
                return !element || !element.value?.trim();
            });

            if (missingFields.length > 0) {
                const missingFieldLabels = missingFields.map(field => field.label).join(', ');
                this.log('error', `Please fill in all required fields: ${missingFieldLabels}`);
                isValid = false;
            }

            // Ensure credentials are properly initialized in config
            if (isValid) {
                const instanceUrl = document.getElementById('mastodonInstance')?.value?.trim();
                if (platform === 'mastodon' && instanceUrl) {
                    if (!instanceUrl.startsWith('http://') && !instanceUrl.startsWith('https://')) {
                        this.log('error', 'Instance URL must start with http:// or https://');
                        return false;
                    }
                    
                    this.config.credentials = {
                        instance_url: instanceUrl,
                        client_id: document.getElementById('mastodonClientId').value.trim(),
                        client_secret: document.getElementById('mastodonClientSecret').value.trim(),
                        access_token: document.getElementById('mastodonToken').value.trim(),
                        gemini_api_key: document.getElementById('geminiApiKey').value.trim()
                    };
                } else if (platform === 'twitter') {
                    this.config.credentials = {
                        api_key: document.getElementById('twitterApiKey').value.trim(),
                        api_secret: document.getElementById('twitterApiSecret').value.trim(),
                        access_token: document.getElementById('twitterAccessToken').value.trim(),
                        access_token_secret: document.getElementById('twitterAccessSecret').value.trim(),
                        bearer_token: document.getElementById('twitterBearerToken').value.trim()
                    };
                }
            }

            return isValid;
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

        async updateDMSettings() {
            if (!this.isRunning) {
                showNotification('Please start the agent first', 'warning');
                return;
            }

            try {
                const dmSettings = {
                    enabled: document.getElementById('dmEnabled').checked,
                    auto_reply: document.getElementById('autoReply').checked,
                    reply_interval: parseInt(document.getElementById('replyInterval').value)
                };

                const response = await fetch(`${this.baseUrl}/update-dm-settings`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(dmSettings)
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Failed to update DM settings');
                }

                const data = await response.json();
                this.config.dm_settings = dmSettings;
                showNotification('DM settings updated successfully', 'success');
            } catch (error) {
                showNotification(`Error: ${error.message}`, 'error');
                console.error('DM settings update error:', error);
            }
        }

        async updateLikeSettings() {
            if (!this.isRunning) {
                showNotification('Please start the agent first', 'warning');
                return;
            }

            try {
                const likeSettings = {
                    enabled: document.getElementById('likeEnabled').checked,
                    max_likes_per_hour: parseInt(document.getElementById('maxLikesPerHour').value),
                    like_probability: parseInt(document.getElementById('likeProbability').value) / 100
                };

                const response = await fetch(`${this.baseUrl}/update-like-settings`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(likeSettings)
                });

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.detail || 'Failed to update like settings');
                }

                const data = await response.json();
                this.config.like_settings = likeSettings;
                showNotification('Like settings updated successfully', 'success');
            } catch (error) {
                showNotification(`Error: ${error.message}`, 'error');
                console.error('Like settings update error:', error);
            }
        }

        async updateAutoPostSettings() {
            if (!this.isRunning) {
                showNotification('Please start the agent first', 'warning');
                return;
            }

            try {
                const autoPostSettings = {
                    enabled: document.getElementById('autoPostEnabled').checked,
                    interval: parseInt(document.getElementById('postInterval').value),
                    max_daily_posts: parseInt(document.getElementById('maxDailyPosts').value)
                };

                // Validate settings
                if (autoPostSettings.interval < 300) {
                    showNotification('Post interval must be at least 300 seconds (5 minutes)', 'error');
                    return;
                }
                if (autoPostSettings.interval > 7200) {
                    showNotification('Post interval cannot exceed 7200 seconds (2 hours)', 'error');
                    return;
                }
                if (autoPostSettings.max_daily_posts < 1 || autoPostSettings.max_daily_posts > 96) {
                    showNotification('Max daily posts must be between 1 and 96', 'error');
                    return;
                }

                const response = await fetch(`${this.baseUrl}/update-auto-post-settings`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Cache-Control': 'no-cache'
                    },
                    body: JSON.stringify(autoPostSettings)
                });

                const data = await response.json();
                if (response.ok) {
                    this.config.auto_post_settings = autoPostSettings;
                    showNotification('Auto-posting settings updated successfully', 'success');
                    // Update metrics display if needed
                    this.updateMetricsDisplay();
                } else {
                    throw new Error(data.detail || 'Failed to update auto-posting settings');
                }
            } catch (error) {
                showNotification(error.message, 'error');
                console.error('Auto-posting settings update error:', error);
            }
        }

        validateRateLimits() {
            const maxPosts = parseInt(document.getElementById('maxPostsPerHour').value);
            const cooldown = parseInt(document.getElementById('cooldownPeriod').value);
            
            if (maxPosts < 1 || maxPosts > 50) {
                showNotification('Max posts per hour must be between 1 and 50', 'error');
                return false;
            }
            
            if (cooldown < 30 || cooldown > 3600) {
                showNotification('Cooldown period must be between 30 and 3600 seconds', 'error');
                return false;
            }
            
            return true;
        }
    }

    // Initialize the controller when the page loads
    document.addEventListener('DOMContentLoaded', () => {
        window.agentController = new AgentController();
    }); 
    async function updatePostStyle() {
        const styleConfig = {
            style: document.getElementById('postStyle').value,
            useEmojis: document.getElementById('postStyleEmojis').checked,
            useHashtags: document.getElementById('useHashtags').checked,
            maxLength: parseInt(document.getElementById('postStyleMaxLength').value)
        };

        try {
            const response = await fetch('/api/update-style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(styleConfig)
            });

            const data = await response.json();
            if (response.ok) {
                showNotification('Style updated successfully', 'success');
            } else {
                showNotification('Error updating style', 'error');
            }
        } catch (error) {
            showNotification('Error connecting to server', 'error');
        }
    }