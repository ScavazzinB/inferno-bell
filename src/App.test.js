import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Inferno Bells/i);
  expect(titleElement).toBeInTheDocument();
});

test('renders footer text', () => {
  render(<App />);
  const footerElement = screen.getByText(/Drop a MIDI file to play it with bells/i);
  expect(footerElement).toBeInTheDocument();
});

test('initial render without midi player', () => {
  render(<App />);
  // MidiPlayer ne devrait pas être présent initialement
  const midiPlayerElement = screen.queryByRole('button', { name: /play/i });
  expect(midiPlayerElement).not.toBeInTheDocument();
});
