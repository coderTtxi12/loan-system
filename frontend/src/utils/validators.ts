/**
 * Document validation utilities for different countries.
 */

/**
 * Validate Spanish DNI/NIE.
 * DNI format: 8 digits + 1 letter
 * NIE format: X/Y/Z + 7 digits + 1 letter
 */
export const validateDNI = (value: string): boolean => {
  const dni = value.toUpperCase().replace(/\s/g, '');
  
  // DNI pattern: 8 digits + letter
  const dniPattern = /^[0-9]{8}[A-Z]$/;
  // NIE pattern: X/Y/Z + 7 digits + letter
  const niePattern = /^[XYZ][0-9]{7}[A-Z]$/;
  
  if (!dniPattern.test(dni) && !niePattern.test(dni)) {
    return false;
  }
  
  // Calculate check letter
  const letters = 'TRWAGMYFPDXBNJZSQVHLCKE';
  let number: number;
  
  if (niePattern.test(dni)) {
    // Convert NIE prefix to number
    const prefix = dni.charAt(0);
    const nieNumber = dni.substring(1, 8);
    const prefixMap: Record<string, string> = { X: '0', Y: '1', Z: '2' };
    number = parseInt(prefixMap[prefix] + nieNumber, 10);
  } else {
    number = parseInt(dni.substring(0, 8), 10);
  }
  
  const expectedLetter = letters[number % 23];
  return dni.charAt(dni.length - 1) === expectedLetter;
};

/**
 * Validate Mexican CURP.
 * Format: 18 characters - AAAA000000HSSSCCX0
 */
export const validateCURP = (value: string): boolean => {
  const curp = value.toUpperCase().replace(/\s/g, '');
  
  // Basic format validation
  const pattern = /^[A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z0-9]\d$/;
  
  if (!pattern.test(curp)) {
    return false;
  }
  
  // Validate birth date portion (positions 4-10: YYMMDD)
  const month = parseInt(curp.substring(6, 8), 10);
  const day = parseInt(curp.substring(8, 10), 10);
  
  if (month < 1 || month > 12 || day < 1 || day > 31) {
    return false;
  }
  
  // Validate state code (positions 11-13)
  const validStates = [
    'AS', 'BC', 'BS', 'CC', 'CL', 'CM', 'CS', 'CH', 'DF', 'DG',
    'GT', 'GR', 'HG', 'JC', 'MC', 'MN', 'MS', 'NT', 'NL', 'OC',
    'PL', 'QT', 'QR', 'SP', 'SL', 'SR', 'TC', 'TS', 'TL', 'VZ',
    'YN', 'ZS', 'NE'
  ];
  
  const stateCode = curp.substring(11, 13);
  return validStates.includes(stateCode);
};

/**
 * Validate Colombian CC (Cédula de Ciudadanía).
 * Format: 6-10 digits
 */
export const validateCC = (value: string): boolean => {
  const cc = value.replace(/\s/g, '').replace(/\./g, '').replace(/-/g, '');
  
  // Must be 6-10 digits
  if (!/^\d{6,10}$/.test(cc)) {
    return false;
  }
  
  // Cannot start with 0
  if (cc.startsWith('0')) {
    return false;
  }
  
  return true;
};

/**
 * Validate Brazilian CPF.
 * Format: 11 digits with check digits
 */
export const validateCPF = (value: string): boolean => {
  const cpf = value.replace(/\D/g, '');
  
  // Must be 11 digits
  if (cpf.length !== 11) {
    return false;
  }
  
  // Check for known invalid CPFs (all same digits)
  if (/^(\d)\1{10}$/.test(cpf)) {
    return false;
  }
  
  // Validate first check digit
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(cpf.charAt(i), 10) * (10 - i);
  }
  let remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(cpf.charAt(9), 10)) {
    return false;
  }
  
  // Validate second check digit
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(cpf.charAt(i), 10) * (11 - i);
  }
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(cpf.charAt(10), 10)) {
    return false;
  }
  
  return true;
};

/**
 * Get validator function by country code.
 */
export const getDocumentValidator = (countryCode: string): ((value: string) => boolean) => {
  const validators: Record<string, (value: string) => boolean> = {
    ES: validateDNI,
    MX: validateCURP,
    CO: validateCC,
    BR: validateCPF,
  };
  
  return validators[countryCode] || (() => true);
};

/**
 * Get document type by country code.
 */
export const getDocumentType = (countryCode: string): string => {
  const types: Record<string, string> = {
    ES: 'DNI',
    MX: 'CURP',
    CO: 'CC',
    BR: 'CPF',
  };
  
  return types[countryCode] || 'ID';
};

/**
 * Get document placeholder by country code.
 */
export const getDocumentPlaceholder = (countryCode: string): string => {
  const placeholders: Record<string, string> = {
    ES: '12345678A',
    MX: 'AAAA000000HSSSCCX0',
    CO: '1234567890',
    BR: '123.456.789-00',
  };
  
  return placeholders[countryCode] || 'Document number';
};

/**
 * Get currency by country code.
 */
export const getCurrency = (countryCode: string): string => {
  const currencies: Record<string, string> = {
    ES: 'EUR',
    MX: 'MXN',
    CO: 'COP',
    BR: 'BRL',
  };
  
  return currencies[countryCode] || 'USD';
};

export default {
  validateDNI,
  validateCURP,
  validateCC,
  validateCPF,
  getDocumentValidator,
  getDocumentType,
  getDocumentPlaceholder,
  getCurrency,
};
