/**
 * WorkSynapse Form Validation Utilities
 * =====================================
 * Comprehensive form validation with field-level errors,
 * regex patterns, and server-side error binding.
 */

// Validation error type
export interface FieldError {
    field: string;
    message: string;
    code?: string;
}

export interface ValidationResult {
    isValid: boolean;
    errors: FieldError[];
    fieldErrors: Record<string, string>;
}

// Validation rules
interface ValidationRule {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    patternMessage?: string;
    custom?: (value: any, allValues?: any) => string | null;
}

// Field validation schema
export interface ValidationSchema {
    [field: string]: ValidationRule;
}

// Common regex patterns
export const patterns = {
    email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/,
    passwordSimple: /^.{8,}$/,
    username: /^[a-zA-Z0-9_-]{3,30}$/,
    phone: /^\+?[1-9]\d{1,14}$/,
    url: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)$/,
    alphanumeric: /^[a-zA-Z0-9]+$/,
    slug: /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
    uuid: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
};

// Validate single field
export function validateField(
    field: string,
    value: any,
    rules: ValidationRule,
    allValues?: any
): FieldError | null {
    // Required check
    if (rules.required) {
        if (value === undefined || value === null || value === '') {
            return { field, message: `${formatFieldName(field)} is required` };
        }
    }

    // Skip other validations if value is empty and not required
    if (!rules.required && (value === undefined || value === null || value === '')) {
        return null;
    }

    const stringValue = String(value);

    // Min length
    if (rules.minLength !== undefined && stringValue.length < rules.minLength) {
        return {
            field,
            message: `${formatFieldName(field)} must be at least ${rules.minLength} characters`,
        };
    }

    // Max length
    if (rules.maxLength !== undefined && stringValue.length > rules.maxLength) {
        return {
            field,
            message: `${formatFieldName(field)} must not exceed ${rules.maxLength} characters`,
        };
    }

    // Pattern
    if (rules.pattern && !rules.pattern.test(stringValue)) {
        return {
            field,
            message: rules.patternMessage || `${formatFieldName(field)} format is invalid`,
        };
    }

    // Custom validation
    if (rules.custom) {
        const customError = rules.custom(value, allValues);
        if (customError) {
            return { field, message: customError };
        }
    }

    return null;
}

// Validate form data against schema
export function validateForm<T extends Record<string, any>>(
    data: T,
    schema: ValidationSchema
): ValidationResult {
    const errors: FieldError[] = [];
    const fieldErrors: Record<string, string> = {};

    for (const [field, rules] of Object.entries(schema)) {
        const error = validateField(field, data[field], rules, data);
        if (error) {
            errors.push(error);
            fieldErrors[field] = error.message;
        }
    }

    return {
        isValid: errors.length === 0,
        errors,
        fieldErrors,
    };
}

// Helper to format field names
function formatFieldName(field: string): string {
    return field
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

// Common validation schemas
export const loginSchema: ValidationSchema = {
    email: {
        required: true,
        pattern: patterns.email,
        patternMessage: 'Please enter a valid email address',
    },
    password: {
        required: true,
        minLength: 1,
    },
};

export const registerSchema: ValidationSchema = {
    email: {
        required: true,
        pattern: patterns.email,
        patternMessage: 'Please enter a valid email address',
    },
    password: {
        required: true,
        minLength: 8,
        pattern: patterns.password,
        patternMessage: 'Password must contain at least 8 characters, one uppercase, one lowercase, one number, and one special character',
    },
    full_name: {
        required: true,
        minLength: 2,
        maxLength: 100,
    },
    username: {
        required: false,
        pattern: patterns.username,
        patternMessage: 'Username must be 3-30 characters, alphanumeric with _ or -',
    },
    confirm_password: {
        required: true,
        custom: (value, allValues) => {
            if (allValues?.password && value !== allValues.password) {
                return 'Passwords do not match';
            }
            return null;
        },
    },
};

export const projectSchema: ValidationSchema = {
    name: {
        required: true,
        minLength: 2,
        maxLength: 100,
    },
    description: {
        required: false,
        maxLength: 1000,
    },
    visibility: {
        required: true,
    },
};

export const taskSchema: ValidationSchema = {
    title: {
        required: true,
        minLength: 2,
        maxLength: 200,
    },
    description: {
        required: false,
        maxLength: 5000,
    },
    priority: {
        required: true,
    },
    status: {
        required: true,
    },
};

export const noteSchema: ValidationSchema = {
    title: {
        required: true,
        minLength: 1,
        maxLength: 200,
    },
    content: {
        required: false,
        maxLength: 50000,
    },
};

// Parse server-side validation errors
export function parseServerErrors(serverErrors: any): Record<string, string> {
    const fieldErrors: Record<string, string> = {};

    if (Array.isArray(serverErrors)) {
        // Pydantic validation errors
        for (const error of serverErrors) {
            const field = error.loc?.[error.loc.length - 1] || 'unknown';
            fieldErrors[field] = error.msg || 'Validation error';
        }
    } else if (typeof serverErrors === 'object') {
        // Simple field -> message mapping
        for (const [field, message] of Object.entries(serverErrors)) {
            fieldErrors[field] = String(message);
        }
    }

    return fieldErrors;
}

// useForm custom hook
export interface UseFormOptions<T> {
    initialValues: T;
    validationSchema: ValidationSchema;
    onSubmit: (values: T) => Promise<void>;
}

export interface FormState<T> {
    values: T;
    errors: Record<string, string>;
    touched: Record<string, boolean>;
    isSubmitting: boolean;
    isValid: boolean;
}

// Client-side form state helpers
export function createFormState<T extends Record<string, any>>(
    initialValues: T
): FormState<T> {
    return {
        values: initialValues,
        errors: {},
        touched: {},
        isSubmitting: false,
        isValid: true,
    };
}

export function updateFieldValue<T extends Record<string, any>>(
    state: FormState<T>,
    field: keyof T,
    value: any
): FormState<T> {
    return {
        ...state,
        values: { ...state.values, [field]: value },
        touched: { ...state.touched, [field]: true },
    };
}

export function setFormErrors<T>(
    state: FormState<T>,
    errors: Record<string, string>
): FormState<T> {
    return {
        ...state,
        errors,
        isValid: Object.keys(errors).length === 0,
    };
}
