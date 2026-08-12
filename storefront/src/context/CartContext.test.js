import React from 'react';
import { render, screen } from '@testing-library/react';
import { CartProvider, useCart } from './CartContext';

const TestComponent = () => {
  const { cartItems } = useCart();
  return (
    <div>
      <span data-testid="cart-count">{cartItems.length}</span>
    </div>
  );
};

describe('CartContext Loading Error Handling', () => {
  let consoleErrorMock;
  let getItemMock;

  beforeEach(() => {
    localStorage.clear();
    consoleErrorMock = jest.spyOn(console, 'error').mockImplementation(() => {});
    getItemMock = jest.spyOn(Storage.prototype, 'getItem');
  });

  afterEach(() => {
    consoleErrorMock.mockRestore();
    getItemMock.mockRestore();
    jest.clearAllMocks();
  });

  it('should handle localStorage getItem errors gracefully without crashing', () => {
    const error = new Error('Storage error');
    getItemMock.mockImplementation(() => {
      throw error;
    });

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
    expect(consoleErrorMock).toHaveBeenCalledWith('Error loading cart:', error);
  });

  it('should handle JSON parse errors gracefully without crashing', () => {
    getItemMock.mockImplementation(() => 'invalid-json-data');

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
    expect(consoleErrorMock).toHaveBeenCalled();
    expect(consoleErrorMock.mock.calls[0][0]).toBe('Error loading cart:');
  });

  it('should load cart successfully if JSON is valid', () => {
    const validCart = [{ id: '1', name: 'Product 1', qty: 2 }];
    getItemMock.mockImplementation(() => JSON.stringify(validCart));

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-count')).toHaveTextContent('1');
    expect(consoleErrorMock).not.toHaveBeenCalled();
  });
});
