from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# Core Tables
class Platform(Base):
    __tablename__ = "platforms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    website_url = Column(String(255))
    api_endpoint = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    commission_rate = Column(Float, default=0.0)
    average_delivery_time = Column(Integer)  # in minutes
    minimum_order_value = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=0, index=True)
    image_url = Column(String(255))
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    
    parent = relationship("Category", remote_side="Category.id")
    children = relationship("Category", back_populates="parent")

class Brand(Base):
    __tablename__ = "brands"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    logo_url = Column(String(255))
    website_url = Column(String(255))
    country_of_origin = Column(String(50))
    is_premium = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    brand_id = Column(Integer, ForeignKey("brands.id"), nullable=True, index=True)
    base_unit = Column(String(20))  # kg, liter, piece, etc.
    weight = Column(Float)
    volume = Column(Float)
    dimensions = Column(String(100))  # JSON string
    barcode = Column(String(50), index=True)
    is_organic = Column(Boolean, default=False, index=True)
    is_fresh = Column(Boolean, default=False, index=True)
    shelf_life_days = Column(Integer)
    storage_temperature = Column(String(50))
    nutritional_info = Column(Text)  # JSON string
    allergen_info = Column(Text)
    image_urls = Column(Text)  # JSON array
    tags = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("Category")
    brand = relationship("Brand")

class ProductVariant(Base):
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)  # 1kg, 500g, 2L, etc.
    variant_value = Column(Float, nullable=False)  # 1.0, 0.5, 2.0
    variant_unit = Column(String(20), nullable=False)  # kg, g, L, ml, piece
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    address = Column(Text)
    city = Column(String(50), index=True)
    state = Column(String(50), index=True)
    pincode = Column(String(10), index=True)
    rating = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Pricing and Availability Tables
class ProductPrice(Base):
    __tablename__ = "product_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True, index=True)
    current_price = Column(Float, nullable=False, index=True)
    original_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0, index=True)
    discount_amount = Column(Float, default=0.0)
    is_available = Column(Boolean, default=True, index=True)
    stock_quantity = Column(Integer, default=0, index=True)
    min_order_quantity = Column(Integer, default=1)
    max_order_quantity = Column(Integer, default=100)
    delivery_time_hours = Column(Integer, default=2)
    last_updated = Column(DateTime, default=datetime.utcnow, index=True)
    
    product = relationship("Product")
    variant = relationship("ProductVariant")
    platform = relationship("Platform")
    supplier = relationship("Supplier")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_price_id = Column(Integer, ForeignKey("product_prices.id"), nullable=False, index=True)
    old_price = Column(Float, nullable=False)
    new_price = Column(Float, nullable=False)
    change_percentage = Column(Float)
    reason = Column(String(100))  # promotion, stock_change, market_update
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    product_price = relationship("ProductPrice")

class Promotion(Base):
    __tablename__ = "promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    promotion_type = Column(String(50), nullable=False, index=True)  # percentage, fixed_amount, bogo, etc.
    discount_value = Column(Float)
    min_order_value = Column(Float, default=0.0)
    max_discount_amount = Column(Float)
    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    usage_limit = Column(Integer)
    usage_count = Column(Integer, default=0)
    applicable_categories = Column(Text)  # JSON array
    applicable_products = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    platform = relationship("Platform")

class ProductPromotion(Base):
    __tablename__ = "product_promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    promotion_id = Column(Integer, ForeignKey("promotions.id"), nullable=False, index=True)
    final_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product")
    promotion = relationship("Promotion")

# Location and Delivery Tables
class DeliveryZone(Base):
    __tablename__ = "delivery_zones"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    zone_name = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    pincodes = Column(Text)  # JSON array
    delivery_fee = Column(Float, default=0.0)
    free_delivery_threshold = Column(Float)
    average_delivery_time = Column(Integer)  # in minutes
    is_active = Column(Boolean, default=True, index=True)
    
    platform = relationship("Platform")

class PlatformAvailability(Base):
    __tablename__ = "platform_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    delivery_zone_id = Column(Integer, ForeignKey("delivery_zones.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    is_available = Column(Boolean, default=True, index=True)
    estimated_delivery_time = Column(Integer)  # in minutes
    last_checked = Column(DateTime, default=datetime.utcnow, index=True)
    
    platform = relationship("Platform")
    delivery_zone = relationship("DeliveryZone")
    product = relationship("Product")

# User and Order Tables
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    first_name = Column(String(50))
    last_name = Column(String(50))
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    preferred_platforms = Column(Text)  # JSON array
    preferred_categories = Column(Text)  # JSON array
    budget_range = Column(String(50))
    dietary_preferences = Column(Text)  # JSON array
    is_premium = Column(Boolean, default=False)
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

class UserAddress(Base):
    __tablename__ = "user_addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    address_type = Column(String(20), default="home")  # home, office, other
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(50), nullable=False, index=True)
    state = Column(String(50), nullable=False, index=True)
    pincode = Column(String(10), nullable=False, index=True)
    landmark = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    is_default = Column(Boolean, default=False)
    
    user = relationship("User")

class SearchQuery(Base):
    __tablename__ = "search_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # natural_language, filter_based, comparison
    results_count = Column(Integer, default=0)
    execution_time_ms = Column(Integer)
    was_successful = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User")

# Analytics and Insights Tables
class ProductPopularity(Base):
    __tablename__ = "product_popularity"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    search_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    comparison_count = Column(Integer, default=0)
    popularity_score = Column(Float, default=0.0, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    
    product = relationship("Product")
    platform = relationship("Platform")

class PriceAlert(Base):
    __tablename__ = "price_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=True, index=True)
    target_price = Column(Float, nullable=False)
    current_price = Column(Float)
    alert_type = Column(String(20), default="below")  # below, above, change
    is_active = Column(Boolean, default=True, index=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    product = relationship("Product")
    platform = relationship("Platform")

class MarketTrend(Base):
    __tablename__ = "market_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=True, index=True)
    trend_period = Column(String(20), nullable=False)  # daily, weekly, monthly
    average_price = Column(Float)
    price_change_percentage = Column(Float)
    total_products = Column(Integer)
    products_on_discount = Column(Integer)
    average_discount_percentage = Column(Float)
    trend_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    category = relationship("Category")
    platform = relationship("Platform")

# Review and Rating Tables
class ProductReview(Base):
    __tablename__ = "product_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    rating = Column(Float, nullable=False, index=True)
    review_text = Column(Text)
    is_verified_purchase = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    product = relationship("Product")
    platform = relationship("Platform")
    user = relationship("User")

class PlatformRating(Base):
    __tablename__ = "platform_ratings"
    
    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    delivery_rating = Column(Float)
    app_rating = Column(Float)
    customer_service_rating = Column(Float)
    overall_rating = Column(Float, nullable=False, index=True)
    review_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    platform = relationship("Platform")
    user = relationship("User")

# Additional Tables for Complex Queries
class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform1_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    platform2_id = Column(Integer, ForeignKey("platforms.id"), nullable=False)
    price_difference = Column(Float)
    platform1_price = Column(Float)
    platform2_price = Column(Float)
    cheaper_platform_id = Column(Integer, ForeignKey("platforms.id"))
    analysis_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    product = relationship("Product")

class InventoryLevel(Base):
    __tablename__ = "inventory_levels"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    current_stock = Column(Integer, default=0, index=True)
    reserved_stock = Column(Integer, default=0)
    available_stock = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    max_stock_level = Column(Integer, default=1000)
    last_restocked = Column(DateTime)
    next_restock_date = Column(DateTime)
    stock_status = Column(String(20), default="in_stock", index=True)  # in_stock, low_stock, out_of_stock
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    
    product = relationship("Product")
    platform = relationship("Platform")

# Create indexes for performance optimization
Index('idx_product_prices_composite', ProductPrice.product_id, ProductPrice.platform_id, ProductPrice.current_price)
Index('idx_price_history_date_product', PriceHistory.changed_at, PriceHistory.product_price_id)
Index('idx_product_category_brand', Product.category_id, Product.brand_id)
Index('idx_platform_availability_composite', PlatformAvailability.platform_id, PlatformAvailability.product_id, PlatformAvailability.is_available)
Index('idx_search_queries_date_type', SearchQuery.created_at, SearchQuery.query_type)
Index('idx_product_popularity_score_date', ProductPopularity.popularity_score, ProductPopularity.date)
Index('idx_inventory_stock_status', InventoryLevel.stock_status, InventoryLevel.current_stock)
