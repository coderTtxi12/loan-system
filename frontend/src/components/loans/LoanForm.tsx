/**
 * Loan creation form component with dynamic validation.
 */
import { useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button, Card } from '@/components/ui';
import Input from '@/components/ui/Input';
import { 
  getDocumentValidator, 
  getDocumentType, 
  getDocumentPlaceholder,
  getCurrency 
} from '@/utils/validators';
import type { CountryCode, LoanCreateRequest } from '@/types/loan';

interface LoanFormProps {
  onSubmit: (data: LoanCreateRequest) => Promise<void>;
  loading?: boolean;
}

const countries: { code: CountryCode; name: string; flag: string }[] = [
  { code: 'ES', name: 'España', flag: '🇪🇸' },
  { code: 'MX', name: 'México', flag: '🇲🇽' },
  { code: 'CO', name: 'Colombia', flag: '🇨🇴' },
  { code: 'BR', name: 'Brasil', flag: '🇧🇷' },
];

// Base schema with dynamic document validation based on country_code
const loanSchema = z.object({
  country_code: z.enum(['ES', 'MX', 'CO', 'BR'] as const),
  document_number: z
    .string()
    .min(1, 'Document number is required')
    .min(5, 'Document number must be at least 5 characters')
    .max(50, 'Document number must be at most 50 characters'),
  full_name: z
    .string()
    .min(1, 'Full name is required')
    .min(2, 'Name must be at least 2 characters')
    .max(255, 'Name must be at most 255 characters'),
  amount_requested: z
    .number({ invalid_type_error: 'Amount is required' })
    .positive('Amount must be positive')
    .max(10000000, 'Amount too large'),
  monthly_income: z
    .number({ invalid_type_error: 'Income is required' })
    .min(0, 'Income must be 0 or greater')
    .max(10000000, 'Income too large'),
}).superRefine((data, ctx) => {
  // Validate document_number based on selected country_code
  const documentValidator = getDocumentValidator(data.country_code);
  const docType = getDocumentType(data.country_code);
  
  if (!documentValidator(data.document_number)) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: `Invalid ${docType} format`,
      path: ['document_number'],
    });
  }
});

type LoanFormData = z.infer<typeof loanSchema>;

const LoanForm = ({ onSubmit, loading = false }: LoanFormProps) => {
  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    setValue,
    formState: { errors },
    trigger,
  } = useForm<LoanFormData>({
    resolver: zodResolver(loanSchema),
    defaultValues: {
      country_code: 'MX',
      document_number: '',
      full_name: '',
      amount_requested: undefined,
      monthly_income: undefined,
    },
  });

  const selectedCountry = watch('country_code') as CountryCode;
  const currency = getCurrency(selectedCountry);
  const docType = getDocumentType(selectedCountry);
  const docPlaceholder = getDocumentPlaceholder(selectedCountry);

  // Valid document examples for testing (deterministic - always pass)
  const documentExamples: Record<CountryCode, string> = {
    ES: '12345678Z', // DNI válido (checksum: 12345678 % 23 = 0 -> Z, score: 67)
    MX: 'FZPY690627HJCYITG3', // CURP válido (fecha válida: 27/06/69, estado JC válido, score: 746)
    CO: '1000000', // CC válido (6-10 dígitos, score: 654)
    BR: '12345678909', // CPF válido (11 dígitos, score: 757)
  };

  const handleUseExample = () => {
    const example = documentExamples[selectedCountry];
    setValue('document_number', example);
    trigger('document_number'); // Re-validate after setting
  };

  // Clear document number when country changes
  useEffect(() => {
    setValue('document_number', '');
    trigger('document_number');
  }, [selectedCountry, setValue, trigger]);

  const handleFormSubmit = async (data: LoanFormData) => {
    // Add document_type based on selected country
    // Ensure numbers are properly formatted (FastAPI expects Decimal which accepts numbers)
    const submitData: LoanCreateRequest = {
      country_code: data.country_code,
      document_type: getDocumentType(data.country_code) as LoanCreateRequest['document_type'],
      document_number: data.document_number.trim(),
      full_name: data.full_name.trim(),
      amount_requested: Number(data.amount_requested),
      monthly_income: Number(data.monthly_income),
    };
    
    console.log('Submitting loan data:', submitData);
    await onSubmit(submitData);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Country Selection */}
      <Card title="Country" subtitle="Select the country for this loan application">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {countries.map((country) => (
            <label
              key={country.code}
              className={`
                relative flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all
                ${selectedCountry === country.code
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
            >
              <input
                type="radio"
                value={country.code}
                {...register('country_code')}
                className="sr-only"
              />
              <span className="text-2xl">{country.flag}</span>
              <span className="text-sm font-medium text-gray-900">
                {country.name}
              </span>
              {selectedCountry === country.code && (
                <span className="absolute top-2 right-2 text-primary-500">
                  ✓
                </span>
              )}
            </label>
          ))}
        </div>
      </Card>

      {/* Applicant Information */}
      <Card title="Applicant Information" subtitle="Enter the applicant's personal details">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Full Name"
            placeholder="John Doe"
            error={errors.full_name?.message}
            {...register('full_name')}
          />

          <div className="md:col-span-2">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Document Number ({docType})
                </label>
                <button
                  type="button"
                  onClick={handleUseExample}
                  className="text-xs text-primary-600 hover:text-primary-700 font-medium"
                >
                  Use example
                </button>
              </div>
              <Input
                placeholder={docPlaceholder}
                error={errors.document_number?.message}
                helperText={
                  errors.document_number
                    ? undefined
                    : `Example: ${documentExamples[selectedCountry]}`
                }
                {...register('document_number')}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Loan Details */}
      <Card title="Loan Details" subtitle="Specify the loan amount and income">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Controller
            name="amount_requested"
            control={control}
            render={({ field }) => (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Amount Requested ({currency})
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="10000"
                    className={`
                      w-full px-3 py-2 border rounded-lg shadow-sm transition-colors
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                      ${errors.amount_requested ? 'border-red-500' : 'border-gray-300'}
                    `}
                    {...field}
                    onChange={(e) => field.onChange(parseFloat(e.target.value) || undefined)}
                    value={field.value ?? ''}
                  />
                  <span className="absolute right-3 top-2 text-gray-400 text-sm">
                    {currency}
                  </span>
                </div>
                {errors.amount_requested && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.amount_requested.message}
                  </p>
                )}
              </div>
            )}
          />

          <Controller
            name="monthly_income"
            control={control}
            render={({ field }) => (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly Income ({currency})
                </label>
                <div className="relative">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="3000"
                    className={`
                      w-full px-3 py-2 border rounded-lg shadow-sm transition-colors
                      focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500
                      ${errors.monthly_income ? 'border-red-500' : 'border-gray-300'}
                    `}
                    {...field}
                    onChange={(e) => field.onChange(parseFloat(e.target.value) || undefined)}
                    value={field.value ?? ''}
                  />
                  <span className="absolute right-3 top-2 text-gray-400 text-sm">
                    {currency}
                  </span>
                </div>
                {errors.monthly_income && (
                  <p className="mt-1 text-sm text-red-600">
                    {errors.monthly_income.message}
                  </p>
                )}
              </div>
            )}
          />
        </div>
      </Card>

      {/* Submit */}
      <div className="flex justify-end gap-4">
        <Button type="button" variant="ghost" onClick={() => reset()}>
          Reset Form
        </Button>
        <Button type="submit" loading={loading} size="lg">
          {loading ? 'Creating...' : 'Create Loan Application'}
        </Button>
      </div>
    </form>
  );
};

export default LoanForm;
