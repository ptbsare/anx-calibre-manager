// ==================== User Settings Logic ====================
// This file handles user-specific settings including TTS, LLM, 2FA, and profile management

/**
 * Update TTS UI based on selected provider
 */
function updateTTS_UI() {
    const providerSelect = document.getElementById('tts_provider');
    const voiceInput = document.getElementById('tts_voice');
    const provider = providerSelect.value;

    // 1. Toggle visibility of provider-specific settings
    toggleTTSSettings();

    // 2. Set a default voice if the current one is empty
    const currentVoice = voiceInput.value;

    if (!currentVoice ) {
        if (provider === 'edge') {
            voiceInput.value = 'zh-CN-YunjianNeural';
        } else if (provider === 'openai') {
            voiceInput.value = 'alloy';
        }
    }
}

/**
 * Populate all user settings forms with data from the server
 */
async function populateForms() {
    const userRes = await fetch('/api/user_settings');
    const userData = await userRes.json();
    document.getElementById('kindle_email').value = userData.kindle_email || '';
    document.getElementById('send_format_priority').value = (userData.send_format_priority || []).join(', ');
    document.getElementById('theme').value = userData.theme || 'auto';
    document.getElementById('force_epub_conversion').checked = userData.force_epub_conversion;
    document.getElementById('stats_enabled').checked = userData.stats_enabled;
    document.getElementById('stats_public').checked = userData.stats_public;

    // Populate TTS settings
    const ttsProviderSelect = document.getElementById('tts_provider');
    
    // Normalize provider data from backend to frontend's standard ('edge', 'openai')
    let provider = userData.tts_provider;
    if (provider === 'edge_tts') provider = 'edge';
    if (provider === 'openai_tts') provider = 'openai';
    if (!provider) provider = 'edge'; // Default value
    ttsProviderSelect.value = provider;

    document.getElementById('tts_voice').value = userData.tts_voice || '';
    document.getElementById('tts_api_key').value = userData.tts_api_key || '';
    document.getElementById('tts_base_url').value = userData.tts_base_url || '';
    document.getElementById('tts_model').value = userData.tts_model || '';
    document.getElementById('tts_rate').value = userData.tts_rate || '+0%';
    document.getElementById('tts_volume').value = userData.tts_volume || '+0%';
    document.getElementById('tts_pitch').value = userData.tts_pitch || '+0Hz';
    document.getElementById('tts_sentence_pause_ms').value = userData.tts_sentence_pause_ms || '650';
    document.getElementById('tts_paragraph_pause_ms').value = userData.tts_paragraph_pause_ms || '900';
 
     // Populate LLM settings
     document.getElementById('llm_provider').value = userData.llm_provider || 'openai';
    document.getElementById('llm_base_url').value = userData.llm_base_url || '';
    document.getElementById('llm_api_key').value = userData.llm_api_key || '';
    document.getElementById('llm_model').value = userData.llm_model || '';

    const statsEnabledCheckbox = document.getElementById('stats_enabled');
    const statsUrlContainer = document.getElementById('stats_url_container');
    const statsUrlLink = document.getElementById('stats_url');

    function toggleStatsUrl() {
        if (statsEnabledCheckbox.checked) {
            const url = `${window.location.origin}/stats/${userData.username}`;
            statsUrlLink.href = url;
            statsUrlLink.textContent = url;
            statsUrlContainer.style.display = 'block';
        } else {
            statsUrlContainer.style.display = 'none';
        }
    }

    statsEnabledCheckbox.addEventListener('change', toggleStatsUrl);
    toggleStatsUrl(); // Initial check

    if (userData.smtp_from_address) {
        const tipElement = document.getElementById('smtp_from_address_tip');
        tipElement.textContent = t.smtpFromAddressTip.replace('{email}', userData.smtp_from_address);
    }
    update2FAStatus(userData.has_2fa);
    
    if (isAdmin) {
        const globalRes = await fetch('/api/global_settings');
        const globalData = await globalRes.json();
        for (const key in globalData) {
            const el = document.getElementById(key);
            if (el) {
                if (el.type === 'checkbox') {
                    el.checked = globalData[key];
                } else {
                    el.value = globalData[key];
                }
            }
        }
        
        await fetchUsers();
        // 加载邀请码管理
        await loadInviteCodes();
    }
    await fetchMcpTokens();

    // Setup Koreader WebDAV URL
    const koreaderWebDavUrlElement = document.getElementById('koreader-webdav-url');
    if (koreaderWebDavUrlElement) {
        const webdavUrl = `${window.location.origin}/webdav/${userData.username}/`;
        koreaderWebDavUrlElement.textContent = webdavUrl;
        koreaderWebDavUrlElement.addEventListener('click', () => {
            navigator.clipboard.writeText(webdavUrl).then(() => {
                alert(t.webdavCopied);
            }, () => {
                alert(t.copyFailed);
            });
        });
    }

    document.getElementById('settings-loading-overlay').style.display = 'none';
    document.getElementById('userSettings').classList.add('visible');
    
    updateTTS_UI();
    toggleLLMSettings(); // Initial toggle for LLM settings
    
    // Populate LLM settings with defaults if empty
    if (isAdmin) {
        const globalRes = await fetch('/api/global_settings');
        const globalData = await globalRes.json();
        if (!document.getElementById('llm_base_url').value) {
            document.getElementById('llm_base_url').value = globalData.DEFAULT_LLM_BASE_URL || '';
        }
        if (!document.getElementById('llm_model').value) {
            document.getElementById('llm_model').value = globalData.DEFAULT_LLM_MODEL || '';
        }
    }
    
    // Fetch LLM models on initial load if credentials exist
    fetchLLMModels();
}

/**
 * Toggle visibility of TTS settings based on selected provider
 */
function toggleTTSSettings() {
    const provider = document.getElementById('tts_provider').value;
    const edgeSettings = document.querySelectorAll('.edge-setting');
    const openaiSettings = document.querySelectorAll('.openai-setting');

    // Hide all provider-specific settings first
    document.querySelectorAll('.tts-setting').forEach(el => {
        if (!el.classList.contains('edge-setting') && !el.classList.contains('openai-setting')) {
            // This is a common setting, do nothing
        } else {
            el.style.display = 'none';
        }
    });

    // Show settings for the selected provider
    if (provider === 'openai') {
        openaiSettings.forEach(el => el.style.display = 'block');
    } else { // Default to edge
        edgeSettings.forEach(el => el.style.display = 'block');
    }
}

/**
 * Toggle visibility of LLM settings based on selected provider
 */
function toggleLLMSettings() {
    const provider = document.getElementById('llm_provider').value;
    const openaiSettings = document.querySelectorAll('.openai-llm-setting');

    document.querySelectorAll('.llm-setting').forEach(el => {
        el.style.display = 'none';
    });

    if (provider === 'openai') {
        openaiSettings.forEach(el => el.style.display = 'block');
    }
}

/**
 * Update the voice datalist based on selected TTS provider
 */
function updateVoiceDatalist() {
    const provider = document.getElementById('tts_provider').value;
    const datalist = document.getElementById('tts_voice_list');
    
    datalist.innerHTML = '';

    const voices = ttsVoiceLists[provider] || [];

    voices.forEach(voice => {
        const option = document.createElement('option');
        option.value = voice;
        datalist.appendChild(option);
    });
}

/**
 * Update 2FA status display
 * @param {boolean} is_enabled - Whether 2FA is enabled
 */
function update2FAStatus(is_enabled) {
    const statusContainer = document.getElementById('2fa_status_container');
    if (is_enabled) {
        const enabledText = t.twoFAEnabled;
        const disableText = t.disable;
        statusContainer.innerHTML = `<p>${enabledText}</p><button type="button" class="button-danger" onclick="disable2FA()">${disableText}</button>`;
    } else {
        const notEnabledText = t.twoFANotEnabled;
        const enableText = t.enable;
        statusContainer.innerHTML = `<p>${notEnabledText}</p><button type="button" class="button" onclick="setup2FA()">${enableText}</button>`;
    }
}

/**
 * Setup 2FA for the user
 */
window.setup2FA = async function() {
    const response = await fetch('/api/2fa/setup', { method: 'POST' });
    const data = await response.json();
    if (response.ok) {
        document.getElementById('2fa_status_container').style.display = 'none';
        document.getElementById('2fa_setup_container').style.display = 'block';
        document.getElementById('otp_secret_key').textContent = data.secret;
        document.getElementById('qr_code_container').innerHTML = `<img src="${data.qr_code}" alt="QR Code">`;
    } else {
        alert(data.error || t.setup2FAFailed);
    }
}

/**
 * Cancel 2FA setup process
 */
window.cancel2FASetup = function() {
    document.getElementById('2fa_status_container').style.display = 'block';
    document.getElementById('2fa_setup_container').style.display = 'none';
}

/**
 * Verify and enable 2FA with the provided OTP code
 */
window.verify2FA = async function() {
    const otp_code = document.getElementById('otp_code').value;
    const response = await fetch('/api/2fa/verify', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ otp_code: otp_code })
    });
    const result = await response.json();
    alert(result.message || result.error);
    if (response.ok) {
        cancel2FASetup();
        update2FAStatus(true);
    }
}

/**
 * Disable 2FA for the user
 */
window.disable2FA = async function() {
    if (!confirm(t.confirmDisable2FA)) return;
    const response = await fetch('/api/2fa/disable', { method: 'POST' });
    const result = await response.json();
    alert(result.message || result.error);
    if (response.ok) {
        update2FAStatus(false);
    }
}

/**
 * Save user settings to the server
 * @param {Event} event - The form submission event
 */
window.saveUserSettings = async function(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    data.force_epub_conversion = formData.has('force_epub_conversion');
    data.stats_enabled = formData.has('stats_enabled');
    data.stats_public = formData.has('stats_public');
    const response = await fetch('/api/user_settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const result = await response.json();
    alert(result.message || result.error);
    if (response.ok) {
        localStorage.setItem('theme', data.theme);
        (function() {
            const theme = localStorage.getItem('theme') || 'auto';
            if (theme === 'dark') {
                document.documentElement.classList.add('dark-mode');
            } else if (theme === 'light') {
                document.documentElement.classList.remove('dark-mode');
            } else { 
                if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.classList.add('dark-mode');
                } else {
                    document.documentElement.classList.remove('dark-mode');
                }
            }
        })();
    }
}

/**
 * Fetch LLM models from the server based on credentials
 */
async function fetchLLMModels() {
    const baseUrl = document.getElementById('llm_base_url').value;
    const apiKey = document.getElementById('llm_api_key').value;
    const datalist = document.getElementById('llm_model_list');

    if (!baseUrl || !apiKey) {
        datalist.innerHTML = ''; // Clear list if credentials are not set
        return;
    }

    try {
        const response = await fetch('/api/llm/models', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ base_url: baseUrl, api_key: apiKey })
        });

        datalist.innerHTML = ''; // Clear previous options

        if (response.ok) {
            const models = await response.json();
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                datalist.appendChild(option);
            });
        } else {
            const result = await response.json();
            console.error('Failed to fetch LLM models:', result.error);
        }
    } catch (error) {
        console.error('Error fetching LLM models:', error);
    }
}
