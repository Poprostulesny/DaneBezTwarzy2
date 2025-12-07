export interface AnonymizationResult {
  originalText: string;
  anonymizedText: string;
  replacedText: string;
}

// Label colors for UI (used for highlighting $[LABEL] tags)
// Each tag has a unique, consistent color
export const labelColors: Record<string, string> = {
  // Personal identifiers
  NAME: '#e74c3c',           // Red
  SURNAME: '#c0392b',        // Dark Red
  AGE: '#9b59b6',            // Purple
  'DATE-OF-BIRTH': '#8e44ad', // Dark Purple
  DATE: '#3498db',           // Blue
  SEX: '#e91e63',            // Pink
  
  // Sensitive attributes
  RELIGION: '#f39c12',       // Orange
  'POLITICAL-VIEW': '#d35400', // Dark Orange
  ETHNICITY: '#16a085',      // Teal
  'SEXUAL-ORIENTATION': '#e84393', // Magenta
  HEALTH: '#27ae60',         // Green
  RELATIVE: '#2980b9',       // Dark Blue
  
  // Location
  CITY: '#1abc9c',           // Turquoise
  ADDRESS: '#00bcd4',        // Cyan
  
  // Contact
  EMAIL: '#4ecdc4',          // Mint
  PHONE: '#45b7d1',          // Light Blue
  
  // Documents & IDs
  PESEL: '#ff7043',          // Deep Orange
  'DOCUMENT-NUMBER': '#ff5722', // Burnt Orange
  
  // Work & Education
  COMPANY: '#795548',        // Brown
  'SCHOOL-NAME': '#607d8b',  // Blue Grey
  'JOB-TITLE': '#9c27b0',    // Deep Purple
  
  // Financial
  'BANK-ACCOUNT': '#ffc107', // Amber
  'CREDIT-CARD-NUMBER': '#ff9800', // Orange
  
  // Digital identity
  USERNAME: '#00bfa5',       // Teal Accent
  SECRET: '#f44336',         // Bright Red
};

const API_URL = 'http://localhost:3000';

export async function anonymizeText(text: string): Promise<AnonymizationResult> {
  const response = await fetch(`${API_URL}/anonymize`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();

  return {
    originalText: text,
    anonymizedText: data.anonymizedText,
    replacedText: data.replacedText,
  };
}
