import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { CartProvider, useCart } from './CartContext';

// Helper component to consume context in tests
const TestComponent = () => {
  const { cartItems } = useCart();
  return (
    <div>
      <span data-testid="cart-count">{cartItems.length}</span>
      {cartItems.map(item => (
        <div key={item.id} data-testid={`cart-item-${item.id}`}>
          {item.name} - Qty: {item.qty}
        </div>
      ))}
    </div>
  );
};

describe('CartContext', () => {
  let consoleErrorSpy;

  beforeEach(() => {
    // Clear localStorage before each test
    window.localStorage.clear();
    // Spy on console.error
    consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    jest.clearAllMocks();
  });

  it('handles invalid JSON in localStorage gracefully', () => {
    // Set invalid JSON
    window.localStorage.setItem('obscura_cart', '{bad_json}');

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    // Expect console.error to have been called with "Error parsing cart data" and an Error object
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error parsing cart data',
      expect.any(SyntaxError)
    );

    // The cart should initialize empty despite the error
    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
  });

  it('loads valid cart data from localStorage', () => {
    // Set valid JSON
    const validData = [{ id: 1, name: 'Test Product', qty: 2 }];
    window.localStorage.setItem('obscura_cart', JSON.stringify(validData));

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    // No error should be logged
    expect(consoleErrorSpy).not.toHaveBeenCalled();

    // Cart should contain the item
    expect(screen.getByTestId('cart-count')).toHaveTextContent('1');
    expect(screen.getByTestId('cart-item-1')).toHaveTextContent('Test Product - Qty: 2');
  });
});
