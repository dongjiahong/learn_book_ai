/**
 * Authentication hooks for managing auth state and operations
 */
import { useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { apiClient, LoginRequest, RegisterRequest } from '@/lib/api';

export const useAuth = () => {
    const {
        user,
        tokens,
        isAuthenticated,
        isLoading,
        error,
        login: setAuthData,
        logout: clearAuthData,
        setUser,
        setTokens,
        setLoading,
        setError,
        clearError,
    } = useAuthStore();

    const queryClient = useQueryClient();

    // Login mutation
    const loginMutation = useMutation({
        mutationFn: async (credentials: LoginRequest) => {
            setLoading(true);
            clearError();

            try {
                const tokens = await apiClient.login(credentials);
                const user = await apiClient.getCurrentUser(tokens.access_token);
                return { tokens, user };
            } catch (error) {
                throw error;
            } finally {
                setLoading(false);
            }
        },
        onSuccess: ({ tokens, user }) => {
            setAuthData(tokens, user);
            queryClient.invalidateQueries({ queryKey: ['user'] });
        },
        onError: (error: Error) => {
            setError(error.message);
        },
    });

    // Register mutation
    const registerMutation = useMutation({
        mutationFn: async (userData: RegisterRequest) => {
            setLoading(true);
            clearError();

            try {
                const user = await apiClient.register(userData);
                // Auto-login after registration
                const tokens = await apiClient.login({
                    username: userData.username,
                    password: userData.password,
                });
                return { tokens, user };
            } catch (error) {
                throw error;
            } finally {
                setLoading(false);
            }
        },
        onSuccess: ({ tokens, user }) => {
            setAuthData(tokens, user);
            queryClient.invalidateQueries({ queryKey: ['user'] });
        },
        onError: (error: Error) => {
            setError(error.message);
        },
    });

    // Logout mutation
    const logoutMutation = useMutation({
        mutationFn: async () => {
            if (tokens?.access_token) {
                await apiClient.logout(tokens.access_token);
            }
        },
        onSettled: () => {
            clearAuthData();
            queryClient.clear();
        },
    });

    // Refresh token mutation
    const refreshTokenMutation = useMutation({
        mutationFn: async (refreshToken: string) => {
            return apiClient.refreshToken({ refresh_token: refreshToken });
        },
        onSuccess: (newTokens) => {
            setTokens(newTokens);
        },
        onError: () => {
            // If refresh fails, logout user
            clearAuthData();
        },
    });

    // Auto-refresh token when it's about to expire
    const refreshTokenIfNeeded = useCallback(async () => {
        if (!tokens?.refresh_token) return;

        try {
            // Decode JWT to check expiration (simple check)
            const payload = JSON.parse(atob(tokens.access_token.split('.')[1]));
            const currentTime = Date.now() / 1000;

            // Refresh if token expires in less than 5 minutes
            if (payload.exp - currentTime < 300) {
                await refreshTokenMutation.mutateAsync(tokens.refresh_token);
            }
        } catch (error) {
            console.error('Token refresh check failed:', error);
        }
    }, [tokens, refreshTokenMutation]);

    // Set up automatic token refresh
    useEffect(() => {
        if (!isAuthenticated || !tokens) return;

        const interval = setInterval(refreshTokenIfNeeded, 60000); // Check every minute
        return () => clearInterval(interval);
    }, [isAuthenticated, tokens, refreshTokenIfNeeded]);

    // Fetch current user data
    const { data: currentUser } = useQuery({
        queryKey: ['user'],
        queryFn: () => apiClient.getCurrentUser(tokens!.access_token),
        enabled: isAuthenticated && !!tokens?.access_token,
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: (failureCount, error: unknown) => {
            // Don't retry if unauthorized
            const errorWithMessage = error as { message?: string };
            if (errorWithMessage?.message?.includes('401')) {
                clearAuthData();
                return false;
            }
            return failureCount < 3;
        },
    });

    // Update user data when query succeeds
    useEffect(() => {
        if (currentUser && currentUser !== user) {
            setUser(currentUser);
        }
    }, [currentUser, user, setUser]);

    return {
        // State
        user,
        tokens,
        isAuthenticated,
        isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
        error,

        // Actions
        login: loginMutation.mutate,
        register: registerMutation.mutate,
        logout: logoutMutation.mutate,
        clearError,

        // Mutation states
        isLoginPending: loginMutation.isPending,
        isRegisterPending: registerMutation.isPending,
        isLogoutPending: logoutMutation.isPending,
    };
};