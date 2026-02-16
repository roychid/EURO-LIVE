/**
 * EVENT QUEUE SYSTEM
 * Automatically queues and processes match events
 */

class EventQueue {
    constructor() {
        this.queue = [];
        this.processing = false;
        this.processInterval = 2000; // Process every 2 seconds
        this.maxQueueSize = 50;
        this.autoProcess = true;
        this.listeners = [];
        this.startProcessing();
    }

    // Add event to queue
    addEvent(event, match) {
        const queueItem = {
            id: Date.now() + Math.random(),
            type: this.getEventType(event),
            event: event,
            match: match,
            timestamp: new Date(),
            priority: this.getPriority(event),
            processed: false,
            message: null
        };

        this.queue.push(queueItem);

        // Sort by priority (higher = more important)
        this.queue.sort((a, b) => b.priority - a.priority);

        // Limit queue size
        if (this.queue.length > this.maxQueueSize) {
            this.queue = this.queue.slice(0, this.maxQueueSize);
        }

        // Notify listeners
        this.notifyListeners('added', queueItem);
        
        console.log(`📥 Event queued: ${this.getEventType(event)} - Priority: ${queueItem.priority}`);
        return queueItem;
    }

    // Get event priority (10 = highest)
    getPriority(event) {
        if (event.includes('GOAL')) return 10;
        if (event.includes('🟥')) return 9;
        if (event.includes('FULL TIME')) return 8;
        if (event.includes('HALF TIME')) return 7;
        if (event.includes('🟨')) return 6;
        if (event.includes('PENALTY')) return 5;
        if (event.includes('SUBSTITUTION')) return 4;
        return 3;
    }

    // Get event type
    getEventType(event) {
        if (event.includes('GOAL')) return 'goal';
        if (event.includes('🟥')) return 'red_card';
        if (event.includes('🟨')) return 'yellow_card';
        if (event.includes('FULL TIME')) return 'fulltime';
        if (event.includes('HALF TIME')) return 'halftime';
        if (event.includes('PENALTY')) return 'penalty';
        if (event.includes('SUBSTITUTION')) return 'substitution';
        return 'other';
    }

    // Start processing queue
    startProcessing() {
        if (this.processing) return;
        this.processing = true;
        this.processQueue();
        setInterval(() => this.processQueue(), this.processInterval);
    }

    // Process queue
    processQueue() {
        if (!this.autoProcess || this.queue.length === 0) return;

        // Group similar events from same match
        const groups = this.groupEvents();

        groups.forEach(group => {
            const message = this.formatGroupMessage(group);
            
            group.forEach(item => {
                item.processed = true;
                item.message = message;
            });

            // Notify listeners
            this.notifyListeners('processed', group);
        });

        // Remove processed items
        this.queue = this.queue.filter(item => !item.processed);
    }

    // Group related events
    groupEvents() {
        const groups = [];
        const processed = new Set();

        for (let i = 0; i < this.queue.length; i++) {
            if (processed.has(i)) continue;

            const item = this.queue[i];
            const group = [item];
            processed.add(i);

            // Find events from same match within 30 seconds
            for (let j = i + 1; j < this.queue.length; j++) {
                if (processed.has(j)) continue;

                const other = this.queue[j];
                const timeDiff = Math.abs(other.timestamp - item.timestamp) / 1000;

                if (other.match?.id === item.match?.id && timeDiff < 30) {
                    group.push(other);
                    processed.add(j);
                }
            }

            groups.push(group);
        }

        return groups;
    }

    // Format group message
    formatGroupMessage(group) {
        if (group.length === 0) return null;

        const first = group[0];
        const match = first.match;

        if (!match) return first.event;

        const goals = group.filter(g => g.type === 'goal');
        const redCards = group.filter(g => g.type === 'red_card');
        const yellowCards = group.filter(g => g.type === 'yellow_card');

        let message = `🔴 *LIVE: ${match.homeTeam} vs ${match.awayTeam}*\n`;
        message += `⏱️ ${match.minute || 0}' - ${match.status || 'In Progress'}\n\n`;

        if (goals.length > 0) {
            message += `⚽ *GOAL${goals.length > 1 ? 'S' : ''}!*\n`;
            goals.forEach(g => {
                const event = g.event.split('\n')[0];
                message += `${event}\n`;
            });
            message += '\n';
        }

        if (redCards.length > 0) {
            message += `🟥 *RED CARD${redCards.length > 1 ? 'S' : ''}!*\n`;
            redCards.forEach(g => {
                message += `${g.event}\n`;
            });
            message += '\n';
        }

        if (yellowCards.length > 0) {
            message += `🟨 *YELLOW CARD${yellowCards.length > 1 ? 'S' : ''}*\n`;
            yellowCards.forEach(g => {
                message += `${g.event}\n`;
            });
            message += '\n';
        }

        message += `📊 *Score:* ${match.homeScore || 0} - ${match.awayScore || 0}\n`;
        message += `#LiveFootball #${match.competition?.replace(/\s/g, '') || 'Match'}`;

        return message;
    }

    // Add listener
    addListener(callback) {
        this.listeners.push(callback);
    }

    // Notify listeners
    notifyListeners(action, data) {
        this.listeners.forEach(callback => callback(action, data));
    }

    // Get queue stats
    getStats() {
        return {
            total: this.queue.length,
            byType: {
                goal: this.queue.filter(i => i.type === 'goal').length,
                red_card: this.queue.filter(i => i.type === 'red_card').length,
                yellow_card: this.queue.filter(i => i.type === 'yellow_card').length,
                halftime: this.queue.filter(i => i.type === 'halftime').length,
                fulltime: this.queue.filter(i => i.type === 'fulltime').length
            },
            highestPriority: this.queue[0]?.priority || 0
        };
    }

    // Clear queue
    clearQueue() {
        this.queue = [];
        this.notifyListeners('cleared', null);
    }

    // Toggle auto processing
    toggleAutoProcess(enabled) {
        this.autoProcess = enabled;
    }
}

// Initialize globally
const eventQueue = new EventQueue();