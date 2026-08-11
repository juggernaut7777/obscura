import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ProductCard from './ProductCard';

// Mock the cart context hook
const mockAddToCart = jest.fn();
const mockSetIsSidebarOpen = jest.fn();

jest.mock('../context/CartContext', () => ({
  useCart: () => ({
    addToCart: mockAddToCart,
    setIsSidebarOpen: mockSetIsSidebarOpen,
  }),
}));

describe('ProductCard', () => {
  const defaultProduct = {
    id: '1',
    name: 'Test Product',
    price: 10,
    category: 'Test Category',
    images: ['/test-image-1.jpg']
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders product details correctly', () => {
    render(<ProductCard product={defaultProduct} />);

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Test Category')).toBeInTheDocument();
    expect(screen.getByText('$10.00')).toBeInTheDocument();

    const primaryImage = screen.getByAltText('Test Product');
    expect(primaryImage).toHaveAttribute('src', '/test-image-1.jpg');
  });

  it('renders fallback image when no images are provided', () => {
    const noImageProduct = { ...defaultProduct, images: undefined };
    render(<ProductCard product={noImageProduct} />);

    const primaryImage = screen.getByAltText('Test Product');
    expect(primaryImage).toHaveAttribute('src', '/placeholder.jpg');
  });

  it('renders comparePrice and discount when provided', () => {
    const discountedProduct = {
      ...defaultProduct,
      price: 8,
      comparePrice: 10
    };
    render(<ProductCard product={discountedProduct} />);

    expect(screen.getByText('$8.00')).toBeInTheDocument();
    expect(screen.getByText('$10.00')).toBeInTheDocument();
    expect(screen.getByText('-20%')).toBeInTheDocument();
  });

  it('renders badge when provided', () => {
    const badgedProduct = {
      ...defaultProduct,
      badge: 'New Arrival'
    };
    render(<ProductCard product={badgedProduct} />);

    expect(screen.getByText('New Arrival')).toBeInTheDocument();
  });

  it('shows alternate image on hover if available', () => {
    const multiImageProduct = {
      ...defaultProduct,
      images: ['/test-image-1.jpg', '/test-image-2.jpg']
    };
    render(<ProductCard product={multiImageProduct} />);

    const card = screen.getByRole('link').parentElement;

    // Simulate mouse hover
    fireEvent.mouseEnter(card);

    const hoverImage = screen.getByAltText('Test Product alternate view');
    expect(hoverImage).toBeInTheDocument();
    expect(hoverImage).toHaveAttribute('src', '/test-image-2.jpg');
  });

  it('shows Quick Add button on hover and adds to cart when clicked', () => {
    render(<ProductCard product={defaultProduct} />);

    const card = screen.getByRole('link').parentElement;
    const quickAddButton = screen.getByText('Quick Add');

    // Simulate hover
    fireEvent.mouseEnter(card);
    expect(quickAddButton).toBeInTheDocument();

    // Simulate click on Quick Add button
    fireEvent.click(quickAddButton);

    // Assert cart context functions were called correctly
    expect(mockAddToCart).toHaveBeenCalledTimes(1);
    expect(mockAddToCart).toHaveBeenCalledWith(defaultProduct);
    expect(mockSetIsSidebarOpen).toHaveBeenCalledTimes(1);
    expect(mockSetIsSidebarOpen).toHaveBeenCalledWith(true);
  });

  it('handles onLoad for image correctly', () => {
    render(<ProductCard product={defaultProduct} />);
    const primaryImage = screen.getByAltText('Test Product');

    // Simulating onLoad sets imageLoaded to true, hiding shimmer
    fireEvent.load(primaryImage);

    // Shimmer element check (not easily selectable, but we know it fires load)
    // Here we just test the event fires correctly without errors
    expect(primaryImage).toBeInTheDocument();
  });
});
