import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import PageTitle from "../../components/common/PageTitle";
import api from "../../api/axios";
import type { RegisterRequest, RegisterResponse } from "./auth.types";
import styles from "./Auth.module.css";

interface RegisterForm extends RegisterRequest {
  confirmPassword: string;
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegisterForm>();

  const onSubmit = async (data: RegisterForm) => {
    setServerError(null);
    try {
      const payload: RegisterRequest = { email: data.email, password: data.password };
      const response = await api.post<RegisterResponse>("/auth/register", payload);

      if (response.data.message) {
        navigate("/login", { state: { registered: true } });
      }
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "Rejestracja nie powiodła się. Spróbuj ponownie.";
      setServerError(message);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <PageTitle title="Zarejestruj się" />
        <div className={styles.logoWrapper}>
          <span className={styles.logoIcon}>💍</span>
          <h1 className={styles.logoText}>WeddingPlanner</h1>
        </div>

        <h2 className={styles.title}>Utwórz konto</h2>

        <form onSubmit={handleSubmit(onSubmit)} className={styles.form} noValidate>
          <div className={styles.field}>
            <label htmlFor="email" className={styles.label}>
              Email
            </label>
            <input
              id="email"
              type="email"
              className={`${styles.input} ${errors.email ? styles.inputError : ""}`}
              placeholder="twoj@email.com"
              {...register("email", {
                required: "Email jest wymagany.",
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: "Nieprawidłowy format email.",
                },
              })}
            />
            {errors.email && (
              <span className={styles.errorMsg}>{errors.email.message}</span>
            )}
          </div>

          <div className={styles.field}>
            <label htmlFor="password" className={styles.label}>
              Hasło
            </label>
            <input
              id="password"
              type="password"
              className={`${styles.input} ${errors.password ? styles.inputError : ""}`}
              placeholder="••••••••"
              {...register("password", {
                required: "Hasło jest wymagane.",
                minLength: { value: 6, message: "Hasło musi mieć min. 6 znaków." },
              })}
            />
            {errors.password && (
              <span className={styles.errorMsg}>{errors.password.message}</span>
            )}
          </div>

          <div className={styles.field}>
            <label htmlFor="confirmPassword" className={styles.label}>
              Potwierdź hasło
            </label>
            <input
              id="confirmPassword"
              type="password"
              className={`${styles.input} ${errors.confirmPassword ? styles.inputError : ""}`}
              placeholder="••••••••"
              {...register("confirmPassword", {
                required: "Potwierdzenie hasła jest wymagane.",
                validate: (value) =>
                  value === watch("password") || "Hasła nie są zgodne.",
              })}
            />
            {errors.confirmPassword && (
              <span className={styles.errorMsg}>{errors.confirmPassword.message}</span>
            )}
          </div>

          {serverError && <p className={styles.serverError}>{serverError}</p>}

          <button type="submit" className={styles.btn} disabled={isSubmitting}>
            {isSubmitting ? "Rejestrowanie..." : "Zarejestruj się"}
          </button>
        </form>

        <p className={styles.switchText}>
          Masz już konto?{" "}
          <Link to="/login" className={styles.link}>
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}