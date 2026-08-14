import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Dictation through the browser's own Web Speech API. No dependency, and no
 * audio leaves the page beyond whatever the browser itself does.
 *
 * Only Chromium browsers ship this today, behind the `webkit` prefix, so the
 * hook reports `supported` and callers hide the control when it is false.
 */

interface SpeechAlternative {
  transcript: string;
}

interface SpeechResult extends ArrayLike<SpeechAlternative> {
  isFinal: boolean;
}

interface SpeechResultEvent {
  resultIndex: number;
  results: ArrayLike<SpeechResult>;
}

interface SpeechRecognizer {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start(): void;
  stop(): void;
  onresult: ((event: SpeechResultEvent) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
}

type RecognizerConstructor = new () => SpeechRecognizer;

function recognizerConstructor(): RecognizerConstructor | null {
  if (typeof window === 'undefined') return null;
  const scope = window as unknown as {
    SpeechRecognition?: RecognizerConstructor;
    webkitSpeechRecognition?: RecognizerConstructor;
  };
  return scope.SpeechRecognition ?? scope.webkitSpeechRecognition ?? null;
}

export function useDictation(onTranscript: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const [supported] = useState(() => recognizerConstructor() !== null);
  const recognizerRef = useRef<SpeechRecognizer | null>(null);
  const callbackRef = useRef(onTranscript);
  callbackRef.current = onTranscript;

  const stop = useCallback(() => {
    recognizerRef.current?.stop();
    setListening(false);
  }, []);

  const start = useCallback(() => {
    const Recognizer = recognizerConstructor();
    if (!Recognizer) return;
    const recognizer = new Recognizer();
    recognizer.continuous = false;
    recognizer.interimResults = false;
    recognizer.lang = document.documentElement.lang || 'en-US';
    recognizer.onresult = (event) => {
      let text = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) text += result[0].transcript;
      }
      if (text) callbackRef.current(text.trim());
    };
    recognizer.onerror = () => setListening(false);
    recognizer.onend = () => setListening(false);
    recognizerRef.current = recognizer;
    recognizer.start();
    setListening(true);
  }, []);

  useEffect(() => () => recognizerRef.current?.stop(), []);

  return { supported, listening, start, stop };
}
