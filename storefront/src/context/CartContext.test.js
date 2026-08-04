import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CartProvider, useCart } from './CartContext';
import React from 'react';

// A mock component that uses the cart context to test its functionality
const TestComponent = () => {
  const { cartItems, addToCart, updateQty, removeItem, clearCart, cartOpen, setCartOpen } = useCart();

  return (
    <div>
      <div data-testid="cart-open">{cartOpen.toString()}</div>
      <div data-testid="cart-items-count">{cartItems.length}</div>
      <ul data-testid="cart-items">
        {cartItems.map((item) => (
          <li key={item.id} data-testid={`item-${item.id}`}>
            {item.name} - Qty: {item.qty}
          </li>
        ))}
      </ul>

      <button onClick={() => addToCart({ id: 'p1', name: 'Product 1' }, 1)}>
        Add Product 1
      </button>
      <button onClick={() => addToCart({ id: 'p1', name: 'Product 1' }, 2)}>
        Add More Product 1
      </button>
      <button onClick={() => addToCart({ id: 'p2', name: 'Product 2' }, 1)}>
        Add Product 2
      </button>

      <button onClick={() => updateQty('p1', 5)}>Update P1 Qty 5</button>
      <button onClick={() => updateQty('p1', 0)}>Update P1 Qty 0</button>

      <button onClick={() => removeItem('p1')}>Remove P1</button>

      <button onClick={clearCart}>Clear Cart</button>

      <button onClick={() => setCartOpen(false)}>Close Cart</button>
    </div>
  );
};

describe('CartContext', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    // Clear console errors to avoid noise from React mounting missing errors we mock
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('provides initial empty cart state', () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
    expect(screen.getByTestId('cart-open')).toHaveTextContent('false');
  });

  it('loads initial state from localStorage', () => {
    const initialCart = [{ id: 'test-1', name: 'Test Product', qty: 2 }];
    localStorage.setItem('obscura_cart', JSON.stringify(initialCart));

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    // Test that the item loaded from localStorage is rendered
    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
    expect(screen.getByTestId('item-test-1')).toHaveTextContent('Test Product - Qty: 2');
  });

  it('handles invalid localStorage data gracefully', () => {
    localStorage.setItem('obscura_cart', 'invalid-json');

    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
    expect(console.error).toHaveBeenCalled();
  });

  it('adds items to the cart and saves to localStorage', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
    expect(screen.getByTestId('item-p1')).toHaveTextContent('Product 1 - Qty: 1');
    expect(screen.getByTestId('cart-open')).toHaveTextContent('true');

    // Check if it was saved to localStorage
    const savedCart = JSON.parse(localStorage.getItem('obscura_cart'));
    expect(savedCart).toHaveLength(1);
    expect(savedCart[0].id).toBe('p1');
  });

  it('increments quantity when adding an existing item', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1')); // +1
    await user.click(screen.getByText('Add More Product 1')); // +2

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
    expect(screen.getByTestId('item-p1')).toHaveTextContent('Product 1 - Qty: 3');
  });

  it('updates item quantity', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Update P1 Qty 5'));

    expect(screen.getByTestId('item-p1')).toHaveTextContent('Product 1 - Qty: 5');
  });

  it('removes item when quantity is set below 1', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');

    await user.click(screen.getByText('Update P1 Qty 0'));

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
  });

  it('removes an item explicitly', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Add Product 2'));
    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('2');

    await user.click(screen.getByText('Remove P1'));

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('1');
    expect(screen.queryByTestId('item-p1')).toBeNull();
    expect(screen.getByTestId('item-p2')).toBeInTheDocument();
  });

  it('clears all items from the cart', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    await user.click(screen.getByText('Add Product 1'));
    await user.click(screen.getByText('Add Product 2'));
    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('2');

    await user.click(screen.getByText('Clear Cart'));

    expect(screen.getByTestId('cart-items-count')).toHaveTextContent('0');
    expect(screen.queryByTestId('item-p1')).toBeNull();
    expect(screen.queryByTestId('item-p2')).toBeNull();
  });

  it('allows manually toggling cart open state', async () => {
    const user = userEvent.setup();
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );

    // adding item opens cart
    await user.click(screen.getByText('Add Product 1'));
    expect(screen.getByTestId('cart-open')).toHaveTextContent('true');

    await user.click(screen.getByText('Close Cart'));
    expect(screen.getByTestId('cart-open')).toHaveTextContent('false');
  });

  it('throws error when useCart is used outside of provider', () => {
    // Suppress console.error for expected React boundary error
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});

    const ComponentWithoutProvider = () => {
      useCart();
      return <div>Will not render</div>;
    };

    expect(() => render(<ComponentWithoutProvider />)).toThrow('useCart must be used within a CartProvider');

    consoleError.mockRestore();
  });
});
