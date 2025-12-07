export interface AnonymizationResult {
  originalText: string;
  anonymizedText: string;
  replacedText: string;
}

// Label colors for UI (used for highlighting $[LABEL] tags)
export const labelColors: Record<string, string> = {
  NAME: '#ff6b6b',
  EMAIL: '#4ecdc4',
  PHONE: '#45b7d1',
  ADDRESS: '#96ceb4',
  ZIPCODE: '#dda0dd',
  SSN: '#ff8c42',
  DATE: '#98d8c8',
  MONEY: '#f7dc6f',
  ORGANIZATION: '#bb8fce',
  PERSON: '#ff6b6b',
  LOCATION: '#96ceb4',
  ORG: '#bb8fce',
  GPE: '#96ceb4',
  CARDINAL: '#f7dc6f',
  ORDINAL: '#f7dc6f',
  NORP: '#bb8fce',
  FAC: '#96ceb4',
  PRODUCT: '#45b7d1',
  EVENT: '#98d8c8',
  WORK_OF_ART: '#dda0dd',
  LAW: '#ff8c42',
  LANGUAGE: '#4ecdc4',
  QUANTITY: '#f7dc6f',
  PERCENT: '#f7dc6f',
  TIME: '#98d8c8',
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
