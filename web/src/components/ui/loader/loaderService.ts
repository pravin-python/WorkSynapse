type LoaderListener = (isLoading: boolean) => void;

class LoaderService {
    private count = 0;
    private listeners: LoaderListener[] = [];

    show() {
        this.count++;
        this.notify();
    }

    hide() {
        this.count = Math.max(0, this.count - 1);
        this.notify();
    }

    subscribe(listener: LoaderListener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    private notify() {
        const isLoading = this.count > 0;
        this.listeners.forEach(l => l(isLoading));
    }
}

export const loaderService = new LoaderService();
