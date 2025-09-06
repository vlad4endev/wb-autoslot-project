import React, { useState } from 'react';
import { Button } from '@/components/ui/button.jsx';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx';
import { Input } from '@/components/ui/input.jsx';
import { Label } from '@/components/ui/label.jsx';
import { Alert, AlertDescription } from '@/components/ui/alert.jsx';
import { useAuth } from '../contexts/AuthContext';
import { Eye, EyeOff, Phone, Lock, CheckCircle, Mail } from 'lucide-react';

const LoginPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [userExists, setUserExists] = useState(false);
  
  const { login, register } = useAuth();

  const formatPhone = (value) => {
    // Remove all non-digit characters
    const digits = value.replace(/\D/g, '');
    
    // Format as +7 (XXX) XXX-XX-XX
    if (digits.length === 0) return '';
    if (digits.length <= 1) return `+7`;
    if (digits.length <= 4) return `+7 (${digits.slice(1)}`;
    if (digits.length <= 7) return `+7 (${digits.slice(1, 4)}) ${digits.slice(4)}`;
    if (digits.length <= 9) return `+7 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7)}`;
    return `+7 (${digits.slice(1, 4)}) ${digits.slice(4, 7)}-${digits.slice(7, 9)}-${digits.slice(9, 11)}`;
  };

  const handlePhoneChange = (e) => {
    const formatted = formatPhone(e.target.value);
    setPhone(formatted);
  };

  const getCleanPhone = (formattedPhone) => {
    return formattedPhone.replace(/\D/g, '');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setUserExists(false);
    setLoading(true);

    const cleanPhone = getCleanPhone(phone);
    
    if (!isLogin && cleanPhone.length !== 11) {
      setError('Введите корректный номер телефона');
      setLoading(false);
      return;
    }

    if (isLogin && !phone && !email) {
      setError('Введите номер телефона или email');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Пароль должен содержать минимум 6 символов');
      setLoading(false);
      return;
    }

    if (!isLogin && password !== confirmPassword) {
      setError('Пароли не совпадают');
      setLoading(false);
      return;
    }

    // Email validation for registration
    if (!isLogin && email) {
      const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
      if (!emailPattern.test(email)) {
        setError('Введите корректный email адрес');
        setLoading(false);
        return;
      }
    }

    try {
      const result = isLogin 
        ? await login(phone || email, password)
        : await register(cleanPhone, password, email);

      if (result.success) {
        if (!isLogin) {
          setSuccess('Регистрация прошла успешно! Перенаправляем в приложение...');
        } else {
          setSuccess('Вход выполнен успешно! Перенаправляем в приложение...');
        }
        // The user will be automatically redirected to Dashboard by App component
        // Clear form
        setPhone('');
        setEmail('');
        setPassword('');
        setConfirmPassword('');
      } else {
        // Check if user exists error
        if (result.error_code === 'USER_EXISTS') {
          setUserExists(true);
          setError(result.message);
          // Auto switch to login after 3 seconds
          setTimeout(() => {
            setIsLogin(true);
            setError('');
            setUserExists(false);
          }, 3000);
        } else {
          setError(result.error);
        }
      }
    } catch (error) {
      setError('Произошла ошибка. Попробуйте еще раз.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">
            WB AutoSlot
          </CardTitle>
          <CardDescription>
            {isLogin ? 'Войдите в свой аккаунт' : 'Создайте новый аккаунт'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant={userExists ? "default" : "destructive"} className={userExists ? "border-blue-200 bg-blue-50" : ""}>
                <AlertDescription className={userExists ? "text-blue-800" : ""}>
                  {error}
                  {userExists && (
                    <div className="mt-2 text-sm">
                      Автоматически переходим к авторизации через 3 секунды...
                    </div>
                  )}
                </AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-200 bg-green-50">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800">{success}</AlertDescription>
              </Alert>
            )}
            
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="phone">Номер телефона</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="phone"
                    type="tel"
                    placeholder="+7 (___) ___-__-__"
                    value={phone}
                    onChange={handlePhoneChange}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
            )}

            {isLogin && (
              <div className="space-y-2">
                <Label htmlFor="phone">Номер телефона или Email</Label>
                <div className="relative">
                  {phone && !email ? (
                    <Phone className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  ) : (
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  )}
                  <Input
                    id="phone"
                    type={phone && !email ? "tel" : "text"}
                    placeholder={phone && !email ? "+7 (___) ___-__-__" : "email@example.com или +7 (___) ___-__-__"}
                    value={phone || email}
                    onChange={(e) => {
                      const value = e.target.value;
                      if (value.includes('@')) {
                        setEmail(value);
                        setPhone('');
                      } else {
                        setPhone(formatPhone(value));
                        setEmail('');
                      }
                    }}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
            )}

            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="email">Email (необязательно)</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Пароль</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Введите пароль"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Подтвердите пароль</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="Повторите пароль"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="pl-10"
                    required
                  />
                </div>
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full" 
              disabled={loading}
            >
              {loading ? 'Загрузка...' : (isLogin ? 'Войти' : 'Зарегистрироваться')}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setSuccess('');
                setPassword('');
                setConfirmPassword('');
              }}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {isLogin 
                ? 'Нет аккаунта? Зарегистрируйтесь' 
                : 'Уже есть аккаунт? Войдите'
              }
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;

