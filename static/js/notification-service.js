/**
 * PUSH NOTIFICATION SERVICE
 * Shows desktop notifications when scores change
 */

class NotificationService {
    constructor() {
        this.permission = false;
        this.notifications = [];
        this.maxNotifications = 10;
        this.init();
    }

    async init() {
        if (!('Notification' in window)) {
            console.log('This browser does not support notifications');
            return;
        }

        if (Notification.permission === 'granted') {
            this.permission = true;
        } else if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            this.permission = permission === 'granted';
        }
    }

    show(title, options = {}) {
        if (!this.permission) return;

        const defaultOptions = {
            icon: '/favicon.ico',
            badge: '/favicon.ico',
            vibrate: [200, 100, 200],
            silent: false,
            ...options
        };

        try {
            const notification = new Notification(title, defaultOptions);
            
            // Track notification
            this.notifications.unshift({
                id: Date.now(),
                title,
                options: defaultOptions,
                timestamp: new Date()
            });

            // Limit history
            if (this.notifications.length > this.maxNotifications) {
                this.notifications.pop();
            }

            // Auto close after 5 seconds
            setTimeout(() => notification.close(), 5000);

            return notification;
        } catch (error) {
            console.error('Notification error:', error);
        }
    }

    showGoal(match, scorer, minute, assist) {
        const title = `⚽ GOAL! ${match.homeTeam} ${match.homeScore} - ${match.awayScore} ${match.awayTeam}`;
        const body = `${scorer} scores${assist ? ` (assist: ${assist})` : ''} at ${minute}'`;
        
        return this.show(title, {
            body,
            tag: `goal-${match.id}-${minute}`,
            renotify: true,
            silent: false
        });
    }

    showCard(match, player, cardType, minute) {
        const emoji = cardType.includes('Red') ? '🟥' : '🟨';
        const title = `${emoji} CARD! ${match.homeTeam} ${match.homeScore} - ${match.awayScore} ${match.awayTeam}`;
        const body = `${player} receives ${cardType} at ${minute}'`;
        
        return this.show(title, {
            body,
            tag: `card-${match.id}-${minute}`,
            renotify: true
        });
    }

    showHalftime(match) {
        const title = `⏸️ HALF TIME: ${match.homeTeam} ${match.homeScore} - ${match.awayScore} ${match.awayTeam}`;
        return this.show(title, {
            body: `The first half has ended. Join us for the second half!`,
            tag: `ht-${match.id}`,
            renotify: true
        });
    }

    showFulltime(match) {
        const title = `✅ FULL TIME: ${match.homeTeam} ${match.homeScore} - ${match.awayScore} ${match.awayTeam}`;
        return this.show(title, {
            body: `The match has ended. Final score: ${match.homeScore} - ${match.awayScore}`,
            tag: `ft-${match.id}`,
            renotify: true
        });
    }

    showScoreChange(oldMatch, newMatch) {
        if (oldMatch.homeScore !== newMatch.homeScore || oldMatch.awayScore !== newMatch.awayScore) {
            const title = `⚽ SCORE CHANGE! ${newMatch.homeTeam} ${newMatch.homeScore} - ${newMatch.awayScore} ${newMatch.awayTeam}`;
            const body = `Score updated at ${newMatch.minute}'`;
            
            return this.show(title, {
                body,
                tag: `score-${newMatch.id}-${Date.now()}`,
                renotify: true
            });
        }
    }

    getHistory() {
        return this.notifications;
    }

    clearHistory() {
        this.notifications = [];
    }
}

// Initialize globally
const notifier = new NotificationService();