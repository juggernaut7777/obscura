import React from 'react';
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CartProvider, useCart } from './CartContext';

// Suppress console.error for expected errors in tests
const originalConsoleError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});
afterAll(() => {
  console.error = originalConsoleError;
});

beforeEach(() => {
  localStorage.clear();
  jest.clearAllMocks();
});

const TestComponent = () => {
  const {
    cartItems,
    cartOpen,
    setCartOpen,
    addToCart,
    updateQty,
    removeItem,
    clearCart,
  } = useCart();

  return (
    <div>
      <div data-testid="cart-open">{cartOpen.toString()}</div>
      <div data-testid="cart-items">{JSON.stringify(cartItems)}</div>

      <button onClick={() => setCartOpen(true)}>Open Cart</button>
      <button onClick={() => addToCart({ id: '1', name: 'Product 1' })}>Add Product 1</button>
      <button onClick={() => addToCart({ id: '1', name: 'Product 1' }, 2)}>Add Product 1 (Qty 2)</button>
      <button onClick={() => updateQty('1', 5)}>Update Qty to 5</button>
      <button onClick={() => updateQty('1', 0)}>Update Qty to 0</button>
      <button onClick={() => removeItem('1')}>Remove Product 1</button>
      <button onClick={() => clearCart()}>Clear Cart</button>
    </div>
  );
};

const ContextErrorComponent = () => {
  useCart();
  return <div>Should throw</div>;
};

describe('CartContext', () => {
  it('should initialize with empty cart and closed state', () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-open')).toHaveTextContent('false');
    expect(screen.getByTestId('cart-items')).toHaveTextContent('[]');
  });

  it('should load initial state from localStorage', () => {
    const initialItems = [{ id: '2', name: 'Product 2', qty: 3 }];
    localStorage.setItem('obscura_cart', JSON.stringify(initialItems));

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-items')).toHaveTextContent(JSON.stringify(initialItems));
  });

  it('should handle invalid JSON in localStorage gracefully', () => {
    localStorage.setItem('obscura_cart', 'invalid-json');

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-items')).toHaveTextContent('[]');
    expect(console.error).toHaveBeenCalledWith('Error parsing cart data', expect.any(SyntaxError));
  });

  it('should add item to cart and open cart', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent(
      JSON.stringify([{ id: '1', name: 'Product 1', qty: 1 }])
    );
    expect(screen.getByTestId('cart-open')).toHaveTextContent('true');
    expect(localStorage.getItem('obscura_cart')).toBe(
      JSON.stringify([{ id: '1', name: 'Product 1', qty: 1 }])
    );
  });

  it('should increase quantity if item already exists', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Add Product 1 (Qty 2)'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent(
      JSON.stringify([{ id: '1', name: 'Product 1', qty: 3 }])
    );
  });

  it('should update item quantity', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Update Qty to 5'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent(
      JSON.stringify([{ id: '1', name: 'Product 1', qty: 5 }])
    );
  });

  it('should remove item when updating quantity to less than 1', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Update Qty to 0'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent('[]');
  });

  it('should remove item', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Remove Product 1'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent('[]');
  });

  it('should clear cart', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Clear Cart'));

    expect(screen.getByTestId('cart-items')).toHaveTextContent('[]');
  });

  it('should open cart directly', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Open Cart'));
    expect(screen.getByTestId('cart-open')).toHaveTextContent('true');
  });

  it('should throw error when useCart is used outside CartProvider', () => {
    // Suppress the React error boundary warning for this specific test
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => {
      render(<ContextErrorComponent />);
    }).toThrow('useCart must be used within a CartProvider');

    console.error = originalError;
  });
});
