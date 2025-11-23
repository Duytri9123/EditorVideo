export class ProgressTracker {
    constructor() {
        this.progress = 0;
        this.total = 100;
        this.callbacks = [];
    }

    update(progress, total = null) {
        if (total !== null) {
            this.total = total;
        }
        this.progress = progress;

        this.callbacks.forEach(callback => {
            callback(this.progress, this.total);
        });
    }

    onUpdate(callback) {
        this.callbacks.push(callback);
    }

    reset() {
        this.progress = 0;
        this.total = 100;
    }
}