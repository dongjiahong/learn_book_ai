/**
 * Login form component using React Hook Form and Zod validation
 */
'use client';

import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input, Button, Alert } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';

const loginSchema = z.object({
    username: z.string().min(1, 'Username is required'),
    password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

interface LoginFormProps {
    onSuccess?: () => void;
    onSwitchToRegister?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({
    onSuccess,
    onSwitchToRegister,
}) => {
    const { login, isLoginPending, error, clearError } = useAuth();

    const {
        control,
        handleSubmit,
        formState: { errors },
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema),
        defaultValues: {
            username: '',
            password: '',
        },
    });

    const onSubmit = (data: LoginFormData) => {
        clearError();
        login(data, {
            onSuccess: () => {
                onSuccess?.();
            },
        });
    };

    return (
        <div className="w-full max-w-md mx-auto">
            <div className="text-center mb-8">
                <h1 className="text-2xl font-bold text-gray-900">登录</h1>
                <p className="text-gray-600 mt-2">登录到您的学习平台账户</p>
            </div>

            {error && (
                <Alert
                    message={error}
                    type="error"
                    showIcon
                    closable
                    onClose={clearError}
                    className="mb-4"
                />
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                    <Controller
                        name="username"
                        control={control}
                        render={({ field }) => (
                            <Input
                                {...field}
                                size="large"
                                placeholder="用户名"
                                prefix={<UserOutlined />}
                                status={errors.username ? 'error' : ''}
                            />
                        )}
                    />
                    {errors.username && (
                        <p className="text-red-500 text-sm mt-1">{errors.username.message}</p>
                    )}
                </div>

                <div>
                    <Controller
                        name="password"
                        control={control}
                        render={({ field }) => (
                            <Input.Password
                                {...field}
                                size="large"
                                placeholder="密码"
                                prefix={<LockOutlined />}
                                status={errors.password ? 'error' : ''}
                            />
                        )}
                    />
                    {errors.password && (
                        <p className="text-red-500 text-sm mt-1">{errors.password.message}</p>
                    )}
                </div>

                <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    loading={isLoginPending}
                    className="w-full"
                >
                    登录
                </Button>
            </form>

            {onSwitchToRegister && (
                <div className="text-center mt-6">
                    <span className="text-gray-600">还没有账户？</span>
                    <Button
                        type="link"
                        onClick={onSwitchToRegister}
                        className="p-0 ml-1"
                    >
                        立即注册
                    </Button>
                </div>
            )}
        </div>
    );
};