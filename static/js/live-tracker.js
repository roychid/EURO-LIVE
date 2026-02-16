/**
 * ENHANCED LIVE MATCH TRACKER
 * Automatically detects score changes and queues events
 */

class LiveMatchTracker {
    constructor() {
        this.matches = new Map(); // Store current match states
        this.lastEventIds = new Map();
        this.updateInterval = 10000; // Check every 10 seconds
        this.isTracking = false;
        this.eventQueue = eventQueue;
        this.notifier = notifier;
        this.onMatchUpdate = null; // Callback for UI updates
    }

    startTracking() {
        if (this.isTracking) return;
        this.isTracking = true;
        this.trackMatches();
        setInterval(() => this.trackMatches(), this.updateInterval);
        console.log('🔴 Live match tracking started');
    }

    async trackMatches() {
        try {
            const response = await fetch('/api/livescores');
            const currentMatches = await response.json();

            // Check each match for changes
            currentMatches.forEach(current => {
                const previous = this.matches.get(current.id);
                
                if (previous) {
                    this.detectChanges(previous, current);
                } else {
                    // New match started
                    this.handleNewMatch(current);
                }

                // Update stored state
                this.matches.set(current.id, current);
            });

            // Check for finished matches
            this.checkFinishedMatches(currentMatches);

            // Trigger UI update
            if (this.onMatchUpdate) {
                this.onMatchUpdate(currentMatches);
            }

        } catch (error) {
            console.error('Error tracking matches:', error);
        }
    }

    detectChanges(oldMatch, newMatch) {
        const oldScore = `${oldMatch.home_team?.score || 0}-${oldMatch.away_team?.score || 0}`;
        const newScore = `${newMatch.home_team?.score || 0}-${newMatch.away_team?.score || 0}`;
        const oldMinute = oldMatch.minute || '0';
        const newMinute = newMatch.minute || '0';

        // Score changed - GOAL!
        if (oldScore !== newScore) {
            this.handleGoal(oldMatch, newMatch);
        }

        // Halftime reached
        if (oldMinute !== '45' && newMinute === '45') {
            this.handleHalftime(newMatch);
        }

        // Fulltime reached
        if (oldMinute !== '90' && newMinute === '90') {
            this.handleFulltime(newMatch);
        }

        // Minute changed (tracking progress)
        if (oldMinute !== newMinute) {
            this.handleMinuteChange(newMatch);
        }
    }

    handleGoal(oldMatch, newMatch) {
        const homeScore = newMatch.home_team?.score || 0;
        const awayScore = newMatch.away_team?.score || 0;
        const homeName = newMatch.home_team?.name || 'Home';
        const awayName = newMatch.away_team?.name || 'Away';
        const minute = newMatch.minute || '0';

        // Create goal message
        let message = `⚽ *GOAL!*\n\n`;
        message += `🏟️ ${homeName} ${homeScore} - ${awayScore} ${awayName}\n`;
        message += `⏱️ ${minute}'\n\n`;
        
        // Try to get scorer from events (would need separate API call)
        // For now, generic goal message
        message += `#Goal #LiveFootball`;

        // Queue the event
        eventQueue.addEvent(message, {
            id: newMatch.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore,
            minute: minute,
            competition: newMatch.competition_name
        });

        // Send push notification
        notifier.showScoreChange(oldMatch, newMatch);
    }

    handleHalftime(match) {
        const homeName = match.home_team?.name || 'Home';
        const awayName = match.away_team?.name || 'Away';
        const homeScore = match.home_team?.score || 0;
        const awayScore = match.away_team?.score || 0;

        const message = `⏸️ *HALF TIME*\n\n` +
                       `🏟️ ${homeName} ${homeScore} - ${awayScore} ${awayName}\n\n` +
                       `⏱️ 45' - First half complete\n\n` +
                       `#Halftime #Football`;

        eventQueue.addEvent(message, {
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore,
            minute: '45',
            competition: match.competition_name
        });

        notifier.showHalftime({
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore
        });
    }

    handleFulltime(match) {
        const homeName = match.home_team?.name || 'Home';
        const awayName = match.away_team?.name || 'Away';
        const homeScore = match.home_team?.score || 0;
        const awayScore = match.away_team?.score || 0;

        const message = `✅ *FULL TIME*\n\n` +
                       `🏟️ ${homeName} ${homeScore} - ${awayScore} ${awayName}\n\n` +
                       `⏱️ Full time result\n\n` +
                       `#FullTime #Result`;

        eventQueue.addEvent(message, {
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore,
            minute: '90',
            competition: match.competition_name
        });

        notifier.showFulltime({
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore
        });
    }

    handleMinuteChange(match) {
        // Could be used for live minute tracking
        // Not showing notifications for every minute
    }

    handleNewMatch(match) {
        const homeName = match.home_team?.name || 'Home';
        const awayName = match.away_team?.name || 'Away';
        const minute = match.minute || '0';

        if (minute !== '0' && minute !== 'NS') {
            const message = `🔴 *MATCH STARTED*\n\n` +
                           `🏟️ ${homeName} vs ${awayName}\n` +
                           `⏱️ Kickoff at ${minute}'\n\n` +
                           `#LiveFootball #Kickoff`;

            eventQueue.addEvent(message, {
                id: match.id,
                homeTeam: homeName,
                awayTeam: awayName,
                homeScore: 0,
                awayScore: 0,
                minute: minute,
                competition: match.competition_name
            });
        }
    }

    checkFinishedMatches(currentMatches) {
        const currentIds = new Set(currentMatches.map(m => m.id));

        this.matches.forEach((match, id) => {
            if (!currentIds.has(id)) {
                // Match has ended (no longer in live list)
                this.handleMatchEnded(match);
                this.matches.delete(id);
                this.lastEventIds.delete(id);
            }
        });
    }

    handleMatchEnded(match) {
        const homeName = match.home_team?.name || 'Home';
        const awayName = match.away_team?.name || 'Away';
        const homeScore = match.home_team?.score || 0;
        const awayScore = match.away_team?.score || 0;

        const message = `✅ *MATCH COMPLETED*\n\n` +
                       `🏟️ ${homeName} ${homeScore} - ${awayScore} ${awayName}\n\n` +
                       `⏱️ Full time result\n\n` +
                       `#FinalScore #Football`;

        eventQueue.addEvent(message, {
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore,
            minute: 'FT',
            competition: match.competition_name
        });

        notifier.showFulltime({
            id: match.id,
            homeTeam: homeName,
            awayTeam: awayName,
            homeScore: homeScore,
            awayScore: awayScore
        });
    }

    getMatch(matchId) {
        return this.matches.get(matchId);
    }

    getAllMatches() {
        return Array.from(this.matches.values());
    }

    stopTracking() {
        this.isTracking = false;
    }

    setOnMatchUpdate(callback) {
        this.onMatchUpdate = callback;
    }
}

// Initialize globally
const liveTracker = new LiveMatchTracker();