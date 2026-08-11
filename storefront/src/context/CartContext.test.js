import { render, screen } from '@testing-library/react';
import { CartProvider, useCart } from './CartContext';
import userEvent from '@testing-library/user-event';
import React from 'react';

// Test component to access context
const TestComponent = () => {
  const { cartItems, addToCart, updateQty, removeItem, clearCart, cartOpen } = useCart();
  return (
    <div>
      <div data-testid="cart-count">{cartItems.length}</div>
      <div data-testid="cart-open">{cartOpen.toString()}</div>
      <button onClick={() => addToCart({ id: 1, name: 'Test Product', price: 10 }, 2)}>Add Product 1</button>
      <button onClick={() => updateQty(1, 5)}>Update Qty</button>
      <button onClick={() => removeItem(1)}>Remove Product</button>
      <button onClick={() => clearCart()}>Clear Cart</button>
    </div>
  );
};

describe('CartContext', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('initializes with empty cart and closed state', () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
    expect(screen.getByTestId('cart-open')).toHaveTextContent('false');
  });

  it('loads cart from localStorage on mount', () => {
    localStorage.setItem('obscura_cart', JSON.stringify([{ id: 1, name: 'Saved Product', qty: 1 }]));
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    expect(screen.getByTestId('cart-count')).toHaveTextContent('1');
  });

  it('adds item to cart and opens cart', async () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    await userEvent.click(screen.getByText('Add Product 1'));
    expect(screen.getByTestId('cart-count')).toHaveTextContent('1');
    expect(screen.getByTestId('cart-open')).toHaveTextContent('true');
    expect(JSON.parse(localStorage.getItem('obscura_cart'))[0].qty).toBe(2);
  });

  it('updates item quantity', async () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    await userEvent.click(screen.getByText('Add Product 1'));
    await userEvent.click(screen.getByText('Update Qty'));
    expect(JSON.parse(localStorage.getItem('obscura_cart'))[0].qty).toBe(5);
  });

  it('removes item from cart', async () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    await userEvent.click(screen.getByText('Add Product 1'));
    await userEvent.click(screen.getByText('Remove Product'));
    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
  });

  it('clears the cart', async () => {
    render(
      <CartProvider>
        <TestComponent />
      </CartProvider>
    );
    await userEvent.click(screen.getByText('Add Product 1'));
    await userEvent.click(screen.getByText('Clear Cart'));
    expect(screen.getByTestId('cart-count')).toHaveTextContent('0');
  });
});
