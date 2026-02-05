import { useLoaderContext } from './LoaderContext';

export function useLoader() {
    const { isLoading, showLoader, hideLoader } = useLoaderContext();
    return { isLoading, showLoader, hideLoader };
}
