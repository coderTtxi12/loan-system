/**
 * Typed Redux hooks for use throughout the app.
 */
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './index';

/**
 * Typed version of useDispatch hook.
 * Use this instead of plain `useDispatch`.
 */
export const useAppDispatch = () => useDispatch<AppDispatch>();

/**
 * Typed version of useSelector hook.
 * Use this instead of plain `useSelector`.
 */
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
