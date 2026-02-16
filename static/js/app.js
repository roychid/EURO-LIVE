/**
 * EUROPEAN FOOTBALL DASHBOARD - COMPLETE VERSION
 * - Live scores with REAL scores
 * - Match events with goal scorers and assists
 * - Dual WhatsApp panels (Auto + Manual)
 * - Push notifications
 */

const STATE = {
    currentTab: 'live',
    currentCompetition: 2,
    liveMatches: [],
    fixtures: [],
    standings: {},
    messagesGenerated: 0,
    competitions: {
        2: { name: "Premier League", country: "England", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
        3: { name: "LaLiga", country: "Spain", flag: "🇪🇸" },
        1: { name: "Bundesliga", country: "Germany", flag: "🇩🇪" },
        4: { name: "Serie A", country: "Italy", flag: "🇮🇹" },
        5: { name: "Ligue 1", country: "France", flag: "🇫🇷" },
        196: { name: "Eredivisie", country: "Netherlands", flag: "🇳🇱" },
        8: { name: "Primeira Liga", country: "Portugal", flag: "🇵🇹" },
        68: { name: "Jupiler Pro League", country: "Belgium", flag: "🇧🇪" },
        75: { name: "Scottish Premiership", country: "Scotland", flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿" },
        40: { name: "Danish Superliga", country: "Denmark", flag: "🇩🇰" },
        244: { name: "UEFA Champions League", country: "Europe", flag: "🇪🇺" },
        245: { name: "UEFA Europa League", country: "Europe", flag: "🇪🇺" },
        446: { name: "UEFA Conference League", country: "Europe", flag: "🇪🇺" }
    }
};

const DOM = {
    liveMatches: document.getElementById('liveMatchesList'),
    fixturesList: document.getElementById('fixturesList'),
    standingsTable: document.getElementById('standingsTable'),
    uefaGrid: document.getElementById('uefaGrid'),
    competitionSelector: document.getElementById('competitionSelector'),
    liveCount: document.getElementById('liveCount'),
    liveCountHeader: document.getElementById('liveCountHeader'),
    fixturesCount: document.getElementById('fixturesCount'),
    fixturesCountHeader: document.getElementById('fixturesCountHeader'),
    messagesCount: document.getElementById('messagesCount'),
    liveEventMessages: document.getElementById('liveEventMessages'),
    manualMessage: document.getElementById('manualWhatsappMessage'),
    manualStats: document.getElementById('manualMessageStats'),
    queueBadge: document.getElementById('queueBadge'),
    queueStats: document.getElementById('queueStats'),
    notificationBanner: document.getElementById('notificationBanner')
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 European Football Dashboard starting...');
    
    loadLiveMatches();
    loadTodayFixtures();
    loadUEFACompetitions();
    setupNavigation();
    setupLeagueSelector();
    
    // Setup queue listeners
    setupQueueListeners();
    
    // Start live tracker
    liveTracker.setOnMatchUpdate(handleMatchUpdate);
    liveTracker.startTracking();
    
    // Check notification permission
    if (Notification && Notification.permission === 'default') {
        DOM.notificationBanner.style.display = 'block';
    }
    
    // Auto-refresh intervals
    setInterval(() => {
        if (STATE.currentTab === 'live') {
            loadLiveMatches();
        }
    }, 15000);
    
    setInterval(() => {
        if (STATE.currentTab === 'fixtures') {
            loadTodayFixtures();
        }
    }, 300000);
});

async function fetchAPI(endpoint) {
    try {
        const response = await fetch(endpoint);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Error: ${endpoint}`, error);
        return null;
    }
}

// ==================== QUEUE SETUP ====================

function setupQueueListeners() {
    eventQueue.addListener((action, data) => {
        updateQueueUI();
        
        if (action === 'processed') {
            displayLiveEvent(data);
        }
    });
}

function updateQueueUI() {
    const stats = eventQueue.getStats();
    if (DOM.queueBadge) {
        DOM.queueBadge.textContent = stats.total;
        DOM.queueBadge.style.background = stats.total > 0 ? '#ff4444' : '#666';
    }
    
    if (DOM.queueStats) {
        DOM.queueStats.innerHTML = `${stats.total} pending · ⚽ ${stats.byType.goal} 🟥 ${stats.byType.red_card} 🟨 ${stats.byType.yellow_card}`;
    }
}

function displayLiveEvent(group) {
    if (!DOM.liveEventMessages) return;
    
    const message = group[0]?.message || group[0]?.event;
    if (!message) return;
    
    const timestamp = new Date().toLocaleTimeString();
    
    const eventDiv = document.createElement('div');
    eventDiv.className = 'live-event';
    eventDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span style="color: #ff4444; font-weight: bold;">⚡ LIVE EVENT</span>
            <span style="color: #666; font-size: 0.8rem;">${timestamp}</span>
        </div>
        <pre>${message}</pre>
    `;
    
    DOM.liveEventMessages.prepend(eventDiv);
    
    // Limit to 10 events
    while (DOM.liveEventMessages.children.length > 10) {
        DOM.liveEventMessages.removeChild(DOM.liveEventMessages.lastChild);
    }
}

function handleMatchUpdate(matches) {
    // Update UI if needed
    console.log(`📊 Matches updated: ${matches.length} live`);
}

// ==================== QUEUE FUNCTIONS ====================

function processQueueNow() {
    eventQueue.processQueue();
    showToast('Processing queue...', 'info');
}

function clearQueue() {
    eventQueue.clearQueue();
    if (DOM.liveEventMessages) {
        DOM.liveEventMessages.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bolt"></i>
                <p>Waiting for live events...</p>
                <small>Goals, cards, and updates will appear here automatically</small>
            </div>
        `;
    }
    updateQueueUI();
    showToast('Queue cleared', 'info');
}

function copyLiveEvents() {
    const events = DOM.liveEventMessages?.querySelectorAll('.live-event pre');
    
    if (!events || events.length === 0) {
        showToast('No events to copy', 'warning');
        return;
    }
    
    let message = `⚡ *LIVE MATCH EVENTS* ⚡\n`;
    message += `📅 ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}\n`;
    message += `━━━━━━━━━━━━━━━━━━━━\n\n`;
    
    events.forEach((event, index) => {
        message += event.textContent + '\n';
        if (index < events.length - 1) message += '---\n';
    });
    
    navigator.clipboard.writeText(message).then(() => {
        showToast('✅ Copied events to clipboard!');
    }).catch(() => {
        showToast('❌ Failed to copy', 'error');
    });
}

function shareLiveEvents() {
    const events = DOM.liveEventMessages?.querySelectorAll('.live-event pre');
    
    if (!events || events.length === 0) {
        showToast('No events to share', 'warning');
        return;
    }
    
    let message = `⚡ *LIVE MATCH EVENTS* ⚡\n`;
    message += `📅 ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}\n\n`;
    
    events.forEach((event, index) => {
        message += event.textContent + '\n';
        if (index < events.length - 1) message += '---\n';
    });
    
    const encoded = encodeURIComponent(message);
    window.open(`https://wa.me/?text=${encoded}`, '_blank');
}

function clearLiveEvents() {
    if (DOM.liveEventMessages) {
        DOM.liveEventMessages.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bolt"></i>
                <p>Waiting for live events...</p>
                <small>Goals, cards, and updates will appear here automatically</small>
            </div>
        `;
    }
    showToast('Live events cleared', 'info');
}

// ==================== MANUAL MESSAGE FUNCTIONS ====================

function displayManualMessage(message) {
    if (DOM.manualMessage) {
        DOM.manualMessage.innerHTML = `<pre style="white-space: pre-wrap; font-family: 'Courier New', monospace; margin: 0; color: #e9edef;">${message}</pre>`;
    }
    if (DOM.manualStats) {
        DOM.manualStats.textContent = `${message.length} characters`;
    }
}

function copyManualMessage() {
    const message = DOM.manualMessage?.textContent;
    if (!message || message.includes('Click any "Share"')) {
        showToast('No message to copy', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(message).then(() => {
        showToast('✅ Copied to clipboard!');
    }).catch(() => {
        showToast('❌ Failed to copy', 'error');
    });
}

function sendManualMessage() {
    const message = DOM.manualMessage?.textContent;
    if (!message || message.includes('Click any "Share"')) {
        showToast('No message to send', 'warning');
        return;
    }
    
    const encoded = encodeURIComponent(message);
    window.open(`https://wa.me/?text=${encoded}`, '_blank');
}

function clearManualMessage() {
    if (DOM.manualMessage) {
        DOM.manualMessage.innerHTML = `
            <div class="empty-state">
                <i class="fab fa-whatsapp"></i>
                <p>Click any "Share" button to generate a message</p>
            </div>
        `;
    }
    if (DOM.manualStats) {
        DOM.manualStats.textContent = '0 characters';
    }
}

// ==================== LIVE SCORES ====================

async function loadLiveMatches() {
    if (!DOM.liveMatches) return;
    
    DOM.liveMatches.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading live matches...</p></div>';
    
    const data = await fetchAPI('/api/livescores');
    
    if (data && data.length > 0) {
        STATE.liveMatches = data;
        renderLiveMatches(data);
        if (DOM.liveCount) DOM.liveCount.textContent = data.length;
        if (DOM.liveCountHeader) DOM.liveCountHeader.textContent = data.length;
    } else {
        DOM.liveMatches.innerHTML = '<div class="empty-state"><i class="fas fa-broadcast-tower"></i><p>No live matches at the moment</p></div>';
        if (DOM.liveCount) DOM.liveCount.textContent = '0';
        if (DOM.liveCountHeader) DOM.liveCountHeader.textContent = '0';
    }
}

function renderLiveMatches(matches) {
    let html = '';
    
    matches.forEach(match => {
        const compInfo = STATE.competitions[match.competition_id] || {
            name: match.competition_name || 'Live Match',
            flag: '⚽'
        };
        
        let homeScore = 0;
        let awayScore = 0;
        
        if (match.home_team && match.home_team.score !== undefined) {
            homeScore = parseInt(match.home_team.score) || 0;
            awayScore = parseInt(match.away_team?.score) || 0;
        } else if (match.score_display) {
            const parts = match.score_display.split(' - ');
            if (parts.length === 2) {
                homeScore = parseInt(parts[0]) || 0;
                awayScore = parseInt(parts[1]) || 0;
            }
        }
        
        const homeName = match.home_team?.name || match.home_name || 'Home';
        const awayName = match.away_team?.name || match.away_name || 'Away';
        
        let minuteDisplay = match.minute || '0';
        if (minuteDisplay === 'HT') minuteDisplay = 'HT';
        else if (minuteDisplay === 'FT') minuteDisplay = 'FT';
        else if (minuteDisplay === 'NS') minuteDisplay = '0\'';
        else if (minuteDisplay.includes('+')) minuteDisplay = minuteDisplay;
        else if (!isNaN(parseInt(minuteDisplay))) minuteDisplay = `${minuteDisplay}'`;
        
        const isLive = match.status !== 'FINISHED' && 
                      match.status !== 'NS' && 
                      match.status !== 'Not Started' &&
                      minuteDisplay !== '0\'' &&
                      !minuteDisplay.includes('0\'');
        
        html += `
            <div class="match-row ${isLive ? 'live' : ''}">
                <div class="match-info">
                    <span class="competition-tag">${compInfo.flag} ${compInfo.name}</span>
                    <div class="teams">
                        <span class="team-home">${homeName}</span>
                        <span class="score">${homeScore} - ${awayScore}</span>
                        <span class="team-away">${awayName}</span>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span class="minute">${minuteDisplay}</span>
                    <div class="match-actions">
                        <button class="btn btn-whatsapp btn-sm" onclick="shareLiveScore('${homeName}', '${awayName}', ${homeScore}, ${awayScore}, '${compInfo.name}')">
                            <i class="fab fa-whatsapp"></i> Score
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="showMatchEvents('${match.id}')">
                            <i class="fas fa-list"></i> Events
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    DOM.liveMatches.innerHTML = html;
}

// ==================== MATCH EVENTS ====================

async function showMatchEvents(fixtureId) {
    if (!fixtureId) {
        showToast('Match ID not available', 'error');
        return;
    }
    
    displayManualMessage('⏳ Loading match events...');
    
    const data = await fetchAPI(`/api/match/${fixtureId}/events`);
    
    if (data && data.success && data.events && data.events.length > 0) {
        let message = `⚽ *MATCH EVENTS*\n`;
        message += `🏟️ ${data.match.home.name} vs ${data.match.away.name}\n`;
        message += `📊 Score: ${data.match.score}\n`;
        message += `⏱️ Status: ${data.match.status || 'Full Time'}\n\n`;
        
        const goals = data.events.filter(e => e.type.includes('GOAL') || e.type === 'OWN_GOAL');
        const penalties = data.events.filter(e => e.type === 'GOAL_PENALTY' || e.type === 'MISSED_PENALTY');
        const cards = data.events.filter(e => e.type.includes('CARD'));
        const subs = data.events.filter(e => e.type === 'SUBSTITUTION');
        
        if (goals.length > 0) {
            message += `⚽ *GOALS*\n`;
            goals.forEach(event => {
                message += `${event.description}\n`;
            });
            message += '\n';
        }
        
        if (penalties.length > 0) {
            message += `🥅 *PENALTIES*\n`;
            penalties.forEach(event => {
                message += `${event.description}\n`;
            });
            message += '\n';
        }
        
        if (cards.length > 0) {
            message += `🟨🟥 *CARDS*\n`;
            cards.forEach(event => {
                message += `${event.description}\n`;
            });
            message += '\n';
        }
        
        if (subs.length > 0) {
            message += `🔄 *SUBSTITUTIONS*\n`;
            subs.forEach(event => {
                message += `${event.description}\n`;
            });
        }
        
        message += `\n#MatchEvents #Football`;
        
        displayManualMessage(message);
    } else {
        displayManualMessage(`⚠️ No events available for this match yet.\n\nCheck back during the match for goal scorers and updates!`);
    }
}

// ==================== TODAY'S FIXTURES ====================

async function loadTodayFixtures() {
    if (!DOM.fixturesList) return;
    
    const data = await fetchAPI('/api/fixtures/today');
    
    if (data && data.length > 0) {
        STATE.fixtures = data;
        renderFixtures(data);
        if (DOM.fixturesCount) DOM.fixturesCount.textContent = data.length;
        if (DOM.fixturesCountHeader) DOM.fixturesCountHeader.textContent = data.length;
    } else {
        DOM.fixturesList.innerHTML = '<div class="empty-state"><i class="fas fa-calendar"></i><p>No fixtures scheduled for today</p></div>';
        if (DOM.fixturesCount) DOM.fixturesCount.textContent = '0';
        if (DOM.fixturesCountHeader) DOM.fixturesCountHeader.textContent = '0';
    }
}

function renderFixtures(fixtures) {
    let html = '';
    
    fixtures.forEach(fixture => {
        const compInfo = STATE.competitions[fixture.competition_id] || {
            name: fixture.competition_name || 'Fixture',
            flag: '⚽'
        };
        
        const matchTime = fixture.time ? fixture.time.substring(0, 5) : 'TBD';
        const homeName = fixture.home_team?.name || fixture.home_name || 'Home';
        const awayName = fixture.away_team?.name || fixture.away_name || 'Away';
        
        html += `
            <div class="fixture-row">
                <div class="fixture-info">
                    <span class="competition-tag">${compInfo.flag} ${compInfo.name}</span>
                    <span class="fixture-time">${matchTime}</span>
                    <div class="teams">
                        <span>${homeName}</span>
                        <span style="color: #666;">vs</span>
                        <span>${awayName}</span>
                    </div>
                </div>
                <button class="btn btn-whatsapp btn-sm" onclick="shareFixture('${homeName}', '${awayName}', '${compInfo.name}')">
                    <i class="fab fa-whatsapp"></i> Share
                </button>
            </div>
        `;
    });
    
    DOM.fixturesList.innerHTML = html;
}

// ==================== STANDINGS ====================

async function loadStandings(competitionId) {
    if (!DOM.standingsTable) return;
    
    STATE.currentCompetition = competitionId;
    
    DOM.standingsTable.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading standings...</p></div>';
    
    const data = await fetchAPI(`/api/standings/${competitionId}`);
    
    if (data && data.success && data.standings && data.standings.length > 0) {
        STATE.standings[competitionId] = data.standings;
        renderStandings(data.standings, data.competition);
    } else {
        DOM.standingsTable.innerHTML = '<div class="empty-state"><i class="fas fa-trophy"></i><p>Standings not available at the moment</p></div>';
    }
}

function renderStandings(standings, competition) {
    let html = `
        <div style="background: #1a1a1a; border-radius: 12px; padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h2 style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.8rem;">${competition?.flag || '🏆'}</span>
                    ${competition?.name || 'League'} <span style="color: #666; font-size: 0.9rem; margin-left: 10px;">2025/26</span>
                </h2>
                <div style="display: flex; gap: 10px;">
                    <button class="btn btn-whatsapp" onclick="copyFullTable(${competition?.id})">
                        <i class="fas fa-copy"></i> Copy Table
                    </button>
                    <button class="btn btn-whatsapp" onclick="shareStandings(${competition?.id})">
                        <i class="fab fa-whatsapp"></i> Share
                    </button>
                </div>
            </div>
            <table class="standings-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Team</th>
                        <th>P</th>
                        <th>W</th>
                        <th>D</th>
                        <th>L</th>
                        <th>GF</th>
                        <th>GA</th>
                        <th>GD</th>
                        <th>Pts</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    standings.forEach((team, index) => {
        const position = index + 1;
        const positionClass = position <= 4 ? 'champions-league' : position >= standings.length - 2 ? 'relegation' : '';
        
        html += `
            <tr class="${positionClass}">
                <td class="position">${position}</td>
                <td><strong>${team.team?.name || 'Unknown'}</strong></td>
                <td>${team.played || 0}</td>
                <td>${team.won || 0}</td>
                <td>${team.drawn || 0}</td>
                <td>${team.lost || 0}</td>
                <td>${team.goals_for || 0}</td>
                <td>${team.goals_against || 0}</td>
                <td>${team.goal_difference || 0}</td>
                <td><strong style="color: #25D366;">${team.points || 0}</strong></td>
            </tr>
        `;
    });
    
    html += `
                </tbody>
            </table>
        </div>
    `;
    
    DOM.standingsTable.innerHTML = html;
}

// ==================== UEFA COMPETITIONS ====================

async function loadUEFACompetitions() {
    if (!DOM.uefaGrid) return;
    
    const uefaComps = [
        { id: 244, name: "UEFA Champions League", flag: "🇪🇺", icon: "🏆" },
        { id: 245, name: "UEFA Europa League", flag: "🇪🇺", icon: "🏆" },
        { id: 446, name: "UEFA Conference League", flag: "🇪🇺", icon: "🏆" }
    ];
    
    let html = '';
    uefaComps.forEach(comp => {
        html += `
            <div class="uefa-card" onclick="loadStandings(${comp.id})">
                <div class="uefa-icon">${comp.icon}</div>
                <div class="uefa-name">${comp.name}</div>
                <span style="background: #333; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem;">${comp.flag}</span>
                <p style="margin-top: 12px; color: #aaa; font-size: 0.8rem;">Click to view standings</p>
            </div>
        `;
    });
    
    DOM.uefaGrid.innerHTML = html;
}

// ==================== LEAGUE SELECTOR ====================

function setupLeagueSelector() {
    if (!DOM.competitionSelector) return;
    
    const leagues = [
        { id: 2, name: "Premier League", flag: "🏴󠁧󠁢󠁥󠁮󠁧󠁿" },
        { id: 3, name: "LaLiga", flag: "🇪🇸" },
        { id: 1, name: "Bundesliga", flag: "🇩🇪" },
        { id: 4, name: "Serie A", flag: "🇮🇹" },
        { id: 5, name: "Ligue 1", flag: "🇫🇷" },
        { id: 196, name: "Eredivisie", flag: "🇳🇱" },
        { id: 75, name: "Scotland", flag: "🏴󠁧󠁢󠁳󠁣󠁴󠁿" },
        { id: 40, name: "Denmark", flag: "🇩🇰" }
    ];
    
    let html = '<span style="color: #aaa;">🏆 Select League:</span>';
    leagues.forEach(league => {
        html += `<button class="league-btn ${league.id === STATE.currentCompetition ? 'active' : ''}" onclick="loadStandings(${league.id})">${league.flag} ${league.name}</button>`;
    });
    
    DOM.competitionSelector.innerHTML = html;
}

// ==================== WHATSAPP SHARING ====================

function shareLiveScore(homeTeam, awayTeam, homeScore, awayScore, competition) {
    const now = new Date();
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    
    const message = `⚽ *LIVE SCORE*\n` +
                    `🏆 ${competition}\n` +
                    `🏟️ ${homeTeam} ${homeScore} - ${awayScore} ${awayTeam}\n` +
                    `📅 ${dateStr} · ${timeStr}\n` +
                    `#LiveFootball #Scores`;
    
    displayManualMessage(message);
    showToast('✅ Live score ready for WhatsApp!');
    return message;
}

function shareFixture(homeTeam, awayTeam, competition) {
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    
    const message = `📅 *UPCOMING FIXTURE*\n` +
                    `🏆 ${competition}\n` +
                    `🏟️ ${homeTeam} vs ${awayTeam}\n` +
                    `📆 ${dateStr}\n` +
                    `#Football #Fixtures`;
    
    displayManualMessage(message);
    showToast('✅ Fixture ready for WhatsApp!');
    return message;
}

async function shareStandings(competitionId) {
    const compInfo = STATE.competitions[competitionId];
    if (!compInfo) return;
    
    const response = await fetchAPI(`/api/standings/${competitionId}`);
    
    if (response && response.success && response.standings) {
        const standings = response.standings;
        const now = new Date();
        const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
        
        let message = `🏆 *${compInfo.name} TABLE* 🏆\n`;
        message += `📅 ${dateStr}\n\n`;
        message += `*TOP 5*\n`;
        message += `━━━━━━━━━━\n`;
        
        standings.slice(0, 5).forEach((team, i) => {
            const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`;
            message += `${medal} ${team.team?.name} - *${team.points || 0} pts*\n`;
        });
        
        message += `\n#${compInfo.name.replace(/\s/g, '')} #Standings`;
        
        displayManualMessage(message);
        showToast('✅ Standings ready for WhatsApp!');
        return message;
    }
}

// ==================== COPY ALL FUNCTIONS ====================

function copyAllLiveScores() {
    if (!STATE.liveMatches || STATE.liveMatches.length === 0) {
        showToast('No live matches to copy', 'warning');
        return;
    }
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let message = `⚽ *LIVE FOOTBALL SCORES* ⚽\n`;
    message += `📅 ${dateStr} · ${timeStr}\n`;
    message += `━━━━━━━━━━━━━━━━━━━━\n\n`;
    
    const groupedMatches = {};
    
    STATE.liveMatches.forEach(match => {
        const compId = match.competition_id;
        const compName = STATE.competitions[compId]?.name || match.competition_name || 'Live Match';
        const compFlag = STATE.competitions[compId]?.flag || '⚽';
        
        if (!groupedMatches[compName]) {
            groupedMatches[compName] = {
                flag: compFlag,
                matches: []
            };
        }
        
        let homeScore = 0;
        let awayScore = 0;
        
        if (match.home_team && match.home_team.score !== undefined) {
            homeScore = parseInt(match.home_team.score) || 0;
            awayScore = parseInt(match.away_team?.score) || 0;
        } else if (match.score_display) {
            const parts = match.score_display.split(' - ');
            if (parts.length === 2) {
                homeScore = parseInt(parts[0]) || 0;
                awayScore = parseInt(parts[1]) || 0;
            }
        }
        
        const homeName = match.home_team?.name || match.home_name || 'Home';
        const awayName = match.away_team?.name || match.away_name || 'Away';
        const minute = match.minute || '0';
        
        let minuteDisplay = minute;
        if (minute === 'HT') minuteDisplay = 'HT';
        else if (minute === 'FT') minuteDisplay = 'FT';
        else if (!isNaN(parseInt(minute))) minuteDisplay = `${minute}'`;
        
        groupedMatches[compName].matches.push({
            home: homeName,
            away: awayName,
            homeScore: homeScore,
            awayScore: awayScore,
            minute: minuteDisplay
        });
    });
    
    Object.keys(groupedMatches).sort().forEach(compName => {
        const group = groupedMatches[compName];
        message += `${group.flag} *${compName}*\n`;
        
        group.matches.forEach(match => {
            message += `   ${match.home} ${match.homeScore} - ${match.awayScore} ${match.away}  (${match.minute})\n`;
        });
        message += `\n`;
    });
    
    message += `━━━━━━━━━━━━━━━━━━━━\n`;
    message += `📱 Follow live football updates!\n`;
    message += `#LiveFootball #Scores`;
    
    navigator.clipboard.writeText(message).then(() => {
        showToast(`✅ Copied ${STATE.liveMatches.length} live scores to clipboard!`);
    }).catch(() => {
        showToast('❌ Failed to copy', 'error');
    });
    
    displayManualMessage(message);
}

function copyAllFixtures() {
    if (!STATE.fixtures || STATE.fixtures.length === 0) {
        showToast('No fixtures to copy', 'warning');
        return;
    }
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    
    let message = `📅 *TODAY'S FOOTBALL FIXTURES* 📅\n`;
    message += `📆 ${dateStr}\n`;
    message += `━━━━━━━━━━━━━━━━━━━━\n\n`;
    
    const groupedFixtures = {};
    
    STATE.fixtures.forEach(fixture => {
        const compId = fixture.competition_id;
        const compName = STATE.competitions[compId]?.name || fixture.competition_name || 'Fixture';
        const compFlag = STATE.competitions[compId]?.flag || '⚽';
        
        if (!groupedFixtures[compName]) {
            groupedFixtures[compName] = {
                flag: compFlag,
                fixtures: []
            };
        }
        
        const homeName = fixture.home_team?.name || fixture.home_name || 'Home';
        const awayName = fixture.away_team?.name || fixture.away_name || 'Away';
        const matchTime = fixture.time ? fixture.time.substring(0, 5) : 'TBD';
        
        groupedFixtures[compName].fixtures.push({
            home: homeName,
            away: awayName,
            time: matchTime
        });
    });
    
    Object.keys(groupedFixtures).sort().forEach(compName => {
        const group = groupedFixtures[compName];
        message += `${group.flag} *${compName}*\n`;
        
        group.fixtures.forEach(fixture => {
            message += `   🕒 ${fixture.time} - ${fixture.home} vs ${fixture.away}\n`;
        });
        message += `\n`;
    });
    
    message += `━━━━━━━━━━━━━━━━━━━━\n`;
    message += `⚽ Follow for live scores and updates!\n`;
    message += `#Football #Fixtures #Today`;
    
    navigator.clipboard.writeText(message).then(() => {
        showToast(`✅ Copied ${STATE.fixtures.length} fixtures to clipboard!`);
    }).catch(() => {
        showToast('❌ Failed to copy', 'error');
    });
    
    displayManualMessage(message);
}

function copyFullTable(competitionId) {
    const compInfo = STATE.competitions[competitionId];
    if (!compInfo) {
        showToast('Competition not found', 'error');
        return;
    }
    
    const standings = STATE.standings[competitionId];
    if (!standings || standings.length === 0) {
        showToast('Standings not available', 'warning');
        return;
    }
    
    const now = new Date();
    const dateStr = now.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
    
    let message = `🏆 *${compInfo.flag} ${compInfo.name} TABLE* 🏆\n`;
    message += `📅 ${dateStr}\n`;
    message += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n`;
    message += `Pos | Team | P | W | D | L | GF | GA | GD | Pts\n`;
    message += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    
    standings.forEach((team, index) => {
        const position = index + 1;
        const posDisplay = position.toString().padStart(2, ' ');
        const name = team.team?.name || 'Unknown';
        const shortName = name.length > 15 ? name.substring(0, 12) + '...' : name.padEnd(15, ' ');
        const played = (team.played || 0).toString().padStart(2, ' ');
        const won = (team.won || 0).toString().padStart(2, ' ');
        const drawn = (team.drawn || 0).toString().padStart(2, ' ');
        const lost = (team.lost || 0).toString().padStart(2, ' ');
        const gf = (team.goals_for || 0).toString().padStart(2, ' ');
        const ga = (team.goals_against || 0).toString().padStart(2, ' ');
        const gd = (team.goal_difference || 0).toString().padStart(3, ' ');
        const pts = (team.points || 0).toString().padStart(3, ' ');
        
        message += `${posDisplay} | ${shortName} | ${played} | ${won} | ${drawn} | ${lost} | ${gf} | ${ga} | ${gd} | ${pts}\n`;
    });
    
    message += `━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
    message += `\n#${compInfo.name.replace(/\s/g, '')} #Standings #Football`;
    
    navigator.clipboard.writeText(message).then(() => {
        showToast(`✅ Copied full ${compInfo.name} table to clipboard!`);
    }).catch(() => {
        showToast('❌ Failed to copy', 'error');
    });
    
    displayManualMessage(message);
}

// ==================== NAVIGATION ====================

function setupNavigation() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.getElementById(`${tab}-tab`).classList.add('active');
            
            STATE.currentTab = tab;
            
            if (tab === 'standings') {
                loadStandings(STATE.currentCompetition);
            } else if (tab === 'live') {
                loadLiveMatches();
            } else if (tab === 'fixtures') {
                loadTodayFixtures();
            }
        });
    });
}

// ==================== UTILITY ====================

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: ${type === 'success' ? '#25D366' : '#ff4444'};
        color: white;
        padding: 12px 24px;
        border-radius: 30px;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    `;
    toast.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== GEMINI AI FUNCTIONS - FIXED ====================

// Check Gemini status on load
async function checkGeminiStatus() {
    const statusEl = document.getElementById('geminiStatus');
    if (!statusEl) return;
    
    try {
        const response = await fetch('/api/gemini/status');
        const data = await response.json();
        
        if (data.available) {
            statusEl.innerHTML = '✅ AI Ready';
            statusEl.style.color = '#4ade80';
        } else {
            statusEl.innerHTML = '❌ AI Offline - Check API Key';
            statusEl.style.color = '#f87171';
            console.log('Gemini error:', data.message);
        }
    } catch (error) {
        statusEl.innerHTML = '❌ AI Error';
        statusEl.style.color = '#f87171';
        console.error('Gemini status error:', error);
    }
}

// Enhance live events - FIXED with POST
async function enhanceLiveEvents() {
    const events = document.querySelectorAll('#liveEventMessages .live-event pre');
    
    if (!events || events.length === 0) {
        showToast('No events to enhance', 'warning');
        return;
    }
    
    // Collect all event messages
    const messages = [];
    events.forEach(event => {
        messages.push(event.textContent);
    });
    
    displayManualMessage('🤖 Gemini AI enhancing events...');
    
    try {
        const response = await fetch('/api/gemini/enhance-batch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ messages: messages })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Clear current events
            const container = document.getElementById('liveEventMessages');
            container.innerHTML = '';
            
            // Display enhanced events
            data.enhanced.forEach((enhanced, index) => {
                const timestamp = new Date().toLocaleTimeString();
                const eventDiv = document.createElement('div');
                eventDiv.className = 'live-event';
                eventDiv.innerHTML = `
                    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                        <span style="color: #4285F4; font-weight: bold;">✨ AI ENHANCED</span>
                        <span style="color: #666; font-size: 0.8rem;">${timestamp}</span>
                    </div>
                    <pre>${enhanced}</pre>
                `;
                container.appendChild(eventDiv);
            });
            
            showToast(`✅ Enhanced ${data.enhanced_count} events!`);
        } else {
            showToast('❌ Enhancement failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('❌ Network error', 'error');
        console.error(error);
    }
}

// Translate live events - FIXED with POST
async function translateLiveEvents() {
    const events = document.querySelectorAll('#liveEventMessages .live-event pre');
    const language = document.getElementById('liveLanguageSelect')?.value || 'es';
    
    if (!events || events.length === 0) {
        showToast('No events to translate', 'warning');
        return;
    }
    
    // Combine all events into one message
    let combinedMessage = '';
    events.forEach(event => {
        combinedMessage += event.textContent + '\n---\n';
    });
    
    displayManualMessage('🤖 Gemini AI translating events...');
    
    try {
        const response = await fetch('/api/gemini/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: combinedMessage,
                language: language
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const langNames = {
                'es': 'Spanish', 'fr': 'French', 'de': 'German',
                'it': 'Italian', 'pt': 'Portuguese', 'ar': 'Arabic'
            };
            
            displayManualMessage(`🌍 *TRANSLATED TO ${langNames[language] || language.toUpperCase()}*\n\n${data.translated}`);
            showToast('✅ Translation complete!');
        } else {
            showToast('❌ Translation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('❌ Network error', 'error');
        console.error(error);
    }
}

// Enhance manual message - FIXED with POST
async function enhanceManualMessage() {
    const messageEl = document.getElementById('manualWhatsappMessage');
    const message = messageEl?.textContent;
    
    if (!message || message.includes('Click any "Share"')) {
        showToast('No message to enhance', 'warning');
        return;
    }
    
    displayManualMessage('🤖 Gemini AI enhancing message...');
    
    try {
        const response = await fetch('/api/gemini/enhance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                tone: 'exciting'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayManualMessage(`✨ *AI ENHANCED MESSAGE*\n\n${data.enhanced}`);
            showToast('✅ Message enhanced!');
        } else {
            showToast('❌ Enhancement failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('❌ Network error', 'error');
        console.error(error);
    }
}

// Translate manual message - FIXED with POST
async function translateManualMessage() {
    const messageEl = document.getElementById('manualWhatsappMessage');
    const message = messageEl?.textContent;
    const language = document.getElementById('manualLanguageSelect')?.value || 'es';
    
    if (!message || message.includes('Click any "Share"')) {
        showToast('No message to translate', 'warning');
        return;
    }
    
    displayManualMessage('🤖 Gemini AI translating...');
    
    try {
        const response = await fetch('/api/gemini/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                language: language
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const langNames = {
                'es': 'Spanish', 'fr': 'French', 'de': 'German',
                'it': 'Italian', 'pt': 'Portuguese', 'ar': 'Arabic'
            };
            
            displayManualMessage(`🌍 *TRANSLATED TO ${langNames[language] || language.toUpperCase()}*\n\n${data.translated}`);
            showToast('✅ Translation complete!');
        } else {
            showToast('❌ Translation failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        showToast('❌ Network error', 'error');
        console.error(error);
    }
}

// Show AI match summary - FIXED
async function showAISummary(fixtureId) {
    displayManualMessage('🤖 Gemini AI generating match summary...');
    
    try {
        const response = await fetch(`/api/gemini/match/${fixtureId}/summary`);
        const data = await response.json();
        
        if (data.success) {
            let message = `🤖 *AI MATCH SUMMARY*\n\n`;
            message += `${data.match.home_team?.name || 'Home'} vs ${data.match.away_team?.name || 'Away'}\n`;
            message += `📊 Score: ${data.match.home_score || 0}-${data.match.away_score || 0}\n\n`;
            message += `${data.summary}\n\n`;
            message += `#AIFootball #Gemini`;
            
            displayManualMessage(message);
            showToast('✅ AI summary generated!');
        } else {
            displayManualMessage('❌ Failed to generate AI summary. Check Gemini API key.');
        }
    } catch (error) {
        showToast('❌ Network error', 'error');
        console.error(error);
    }
}

// Initialize Gemini status check on load
document.addEventListener('DOMContentLoaded', function() {
    // Your existing DOMContentLoaded code...
    checkGeminiStatus();
});

// Export functions
window.enhanceLiveEvents = enhanceLiveEvents;
window.translateLiveEvents = translateLiveEvents;
window.enhanceManualMessage = enhanceManualMessage;
window.translateManualMessage = translateManualMessage;
window.showAISummary = showAISummary;

// ==================== NEWS FUNCTIONS ====================

// News state
const newsState = {
    currentNews: [],
    currentCategory: 'sports',
    currentQuery: ''
};

// Load sports news
async function loadSportsNews() {
    const container = document.getElementById('newsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading sports news...</p></div>';
    
    try {
        const response = await fetch('/api/news/sports?limit=20');
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            newsState.currentNews = data.news;
            renderNews(data.news);
            updateActiveButton('sports');
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-newspaper"></i><p>No news available</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load news</p></div>';
        console.error('News error:', error);
    }
}

// Load league news
async function loadLeagueNews(league) {
    const container = document.getElementById('newsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading league news...</p></div>';
    
    try {
        const response = await fetch(`/api/news/league/${league}?limit=20`);
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            newsState.currentNews = data.news;
            renderNews(data.news);
            updateActiveButton(league);
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-newspaper"></i><p>No news available</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load news</p></div>';
    }
}

// Load team news
async function loadTeamNews(team) {
    const container = document.getElementById('newsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading team news...</p></div>';
    
    try {
        const response = await fetch(`/api/news/team/${team}?limit=20`);
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            newsState.currentNews = data.news;
            renderNews(data.news);
            updateActiveButton(team);
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-newspaper"></i><p>No news available</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load news</p></div>';
    }
}

// Load transfer news
async function loadTransferNews() {
    const container = document.getElementById('newsContainer');
    if (!container) return;
    
    container.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading transfer news...</p></div>';
    
    try {
        const response = await fetch('/api/news/transfers?limit=20');
        const data = await response.json();
        
        if (data.success && data.news.length > 0) {
            newsState.currentNews = data.news;
            renderNews(data.news);
            updateActiveButton('transfers');
        } else {
            container.innerHTML = '<div class="empty-state"><i class="fas fa-newspaper"></i><p>No transfer news</p></div>';
        }
    } catch (error) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-circle"></i><p>Failed to load news</p></div>';
    }
}

// Render news
function renderNews(news) {
    const container = document.getElementById('newsContainer');
    if (!container) return;
    
    let html = '';
    news.forEach(article => {
        html += `
            <div class="news-card">
                <img src="${article.image}" class="news-image" alt="${article.title}" 
                     onerror="this.src='https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=600'">
                <div class="news-content">
                    <h3 class="news-title">${article.title}</h3>
                    <p class="news-description">${article.description}</p>
                    <div class="news-meta">
                        <div class="news-source">
                            <i class="fas fa-newspaper"></i>
                            <span>${article.source}</span>
                        </div>
                        <div class="news-date">
                            <i class="far fa-clock"></i>
                            <span>${article.published_at}</span>
                        </div>
                    </div>
                    <div class="news-actions">
                        <button class="btn btn-secondary btn-sm" onclick="window.open('${article.url}', '_blank')">
                            <i class="fas fa-external-link-alt"></i> Read
                        </button>
                        <button class="btn btn-whatsapp btn-sm" onclick="shareNews('${article.id}')">
                            <i class="fab fa-whatsapp"></i> Share
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Update active button
function updateActiveButton(activeId) {
    const buttons = document.querySelectorAll('.league-btn');
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase().includes(activeId) || 
            btn.onclick.toString().includes(activeId)) {
            btn.classList.add('active');
        }
    });
}

// Share news
async function shareNews(newsId) {
    const article = newsState.currentNews.find(a => a.id == newsId);
    if (!article) return;
    
    const message = `📰 *FOOTBALL NEWS*\n\n` +
                   `*${article.title}*\n\n` +
                   `${article.description}\n\n` +
                   `🔗 Read more: ${article.url}\n\n` +
                   `#FootballNews #${article.source.replace(/\s/g, '')}`;
    
    displayManualMessage(message);
    showToast('✅ News ready for WhatsApp!');
}

// Share news digest
async function shareNewsDigest() {
    if (!newsState.currentNews || newsState.currentNews.length === 0) {
        showToast('No news to share', 'warning');
        return;
    }
    
    let message = `📰 *FOOTBALL NEWS DIGEST*\n`;
    message += `📅 ${new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}\n\n`;
    
    newsState.currentNews.slice(0, 5).forEach((article, i) => {
        message += `${i+1}. *${article.title}*\n`;
        message += `   ${article.source} · ${article.published_at}\n\n`;
    });
    
    message += `#FootballNews`;
    
    displayManualMessage(message);
    showToast('✅ News digest ready!');
}

// AI News Summary (using your existing Gemini AI)
async function summarizeNewsWithAI() {
    if (!newsState.currentNews || newsState.currentNews.length === 0) {
        showToast('No news to summarize', 'warning');
        return;
    }
    
    displayManualMessage('🤖 Gemini AI creating news digest...');
    
    try {
        const response = await fetch('/api/gemini/news/summarize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ articles: newsState.currentNews.slice(0, 5) })
        });
        
        const data = await response.json();
        
        if (data.success) {
            displayManualMessage(`🤖 *AI NEWS SUMMARY*\n\n${data.summary}`);
            showToast('✅ AI summary ready!');
        } else {
            showToast('❌ AI summary failed', 'error');
        }
    } catch (error) {
        showToast('❌ AI error', 'error');
        console.error(error);
    }
}

// Initialize news on tab switch (add to your setupNavigation function)
// Add this case to your switch statement:
// case 'news':
//     loadSportsNews();
//     break;

// Export functions
window.loadSportsNews = loadSportsNews;
window.loadLeagueNews = loadLeagueNews;
window.loadTeamNews = loadTeamNews;
window.loadTransferNews = loadTransferNews;
window.shareNews = shareNews;
window.shareNewsDigest = shareNewsDigest;
window.summarizeNewsWithAI = summarizeNewsWithAI;

// ==================== GLOBAL EXPORTS ====================

window.loadStandings = loadStandings;
window.shareLiveScore = shareLiveScore;
window.shareFixture = shareFixture;
window.shareStandings = shareStandings;
window.showMatchEvents = showMatchEvents;
window.copyAllLiveScores = copyAllLiveScores;
window.copyAllFixtures = copyAllFixtures;
window.copyFullTable = copyFullTable;

// Queue functions
window.processQueueNow = processQueueNow;
window.clearQueue = clearQueue;
window.copyLiveEvents = copyLiveEvents;
window.shareLiveEvents = shareLiveEvents;
window.clearLiveEvents = clearLiveEvents;

// Manual message functions
window.copyManualMessage = copyManualMessage;
window.sendManualMessage = sendManualMessage;
window.clearManualMessage = clearManualMessage;
