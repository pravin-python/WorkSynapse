import { useLoader } from './useLoader';
import { useTheme } from '../../../context/ThemeContext';
import './Loader.css';

export function GlobalLoader() {
    const { isLoading } = useLoader();
    const { theme } = useTheme();

    if (!isLoading) return null;

    return (
        <div className={`global-loader-overlay theme-${theme}`}>
            <div className="global-loader-container">
                <div className="loader-animation">
                    <div className="loader-dot"></div>
                    <div className="loader-dot"></div>
                    <div className="loader-dot"></div>
                    <div className="loader-dot"></div>
                </div>
                <span className="loader-text">WorkSynapse</span>
            </div>
        </div>
    );
}
