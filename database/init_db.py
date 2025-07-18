import random
import json
from datetime import datetime, timedelta
from faker import Faker
from database.connection import get_db_session
from database.models import *
from config.settings import Config
import logging

logger = logging.getLogger(__name__)
fake = Faker('en_IN')  # Indian locale for realistic data

class DataGenerator:
    def __init__(self):
        self.db = get_db_session()
        self.platforms_data = []
        self.categories_data = []
        self.brands_data = []
        self.products_data = []
        
    def generate_all_data(self):
        """Generate all initial data"""
        try:
            logger.info("Starting data generation...")
            
            # Core data
            self.generate_platforms()
            self.generate_categories()
            self.generate_brands()
            self.generate_products()
            self.generate_product_variants()
            self.generate_suppliers()
            
            # Pricing and availability
            self.generate_product_prices()
            self.generate_promotions()
            self.generate_delivery_zones()
            self.generate_platform_availability()
            
            # User data
            self.generate_users()
            self.generate_user_addresses()
            
            # Analytics data
            self.generate_product_popularity()
            self.generate_price_history()
            self.generate_market_trends()
            self.generate_inventory_levels()
            
            # Reviews and ratings
            self.generate_product_reviews()
            self.generate_platform_ratings()
            
            # Complex analysis data
            self.generate_competitor_analysis()
            
            self.db.commit()
            logger.info("Data generation completed successfully")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Data generation failed: {e}")
            raise
        finally:
            self.db.close()
    
    def generate_platforms(self):
        """Generate platform data"""
        platforms_info = [
            ("blinkit", "Blinkit", "https://blinkit.com", 10, 0, 39),
            ("zepto", "Zepto", "https://zepto.com", 10, 0, 29),
            ("instamart", "Instamart", "https://instamart.com", 15, 0, 49),
            ("bigbasket_now", "BigBasket Now", "https://bigbasket.com", 30, 100, 0),
            ("dunzo", "Dunzo", "https://dunzo.com", 20, 0, 19),
            ("swiggy_genie", "Swiggy Genie", "https://swiggy.com", 25, 0, 29),
            ("amazon_fresh", "Amazon Fresh", "https://amazon.in", 60, 200, 0),
            ("flipkart_quick", "Flipkart Quick", "https://flipkart.com", 90, 150, 0),
            ("jiomart_express", "JioMart Express", "https://jiomart.com", 120, 250, 0),
            ("grofers", "Grofers", "https://grofers.com", 45, 100, 39)
        ]
        
        for name, display_name, url, delivery_time, min_order, delivery_fee in platforms_info:
            platform = Platform(
                name=name,
                display_name=display_name,
                website_url=url,
                api_endpoint=f"{url}/api/v1",
                average_delivery_time=delivery_time,
                minimum_order_value=min_order,
                delivery_fee=delivery_fee,
                commission_rate=random.uniform(2.0, 8.0)
            )
            self.db.add(platform)
            self.platforms_data.append(platform)
    
    def generate_categories(self):
        """Generate hierarchical category data"""
        main_categories = [
            "Fruits & Vegetables", "Dairy & Eggs", "Meat & Seafood", 
            "Beverages", "Snacks & Branded Foods", "Personal Care",
            "Household Items", "Baby Care", "Pet Care", "Pharma & Wellness"
        ]
        
        subcategories = {
            "Fruits & Vegetables": ["Fresh Fruits", "Fresh Vegetables", "Herbs & Seasonings", "Organic Produce"],
            "Dairy & Eggs": ["Milk", "Cheese", "Yogurt", "Eggs", "Butter & Ghee"],
            "Meat & Seafood": ["Chicken", "Mutton", "Fish", "Prawns", "Eggs"],
            "Beverages": ["Soft Drinks", "Juices", "Tea & Coffee", "Energy Drinks", "Water"],
            "Snacks & Branded Foods": ["Chips & Namkeen", "Biscuits", "Chocolates", "Ready to Cook", "Cereals"],
            "Personal Care": ["Bath & Body", "Hair Care", "Oral Care", "Skin Care", "Feminine Hygiene"],
            "Household Items": ["Cleaning Supplies", "Kitchen Essentials", "Home Decor", "Electronics"],
            "Baby Care": ["Baby Food", "Diapers", "Baby Bath", "Baby Skin Care"],
            "Pet Care": ["Dog Food", "Cat Food", "Pet Accessories", "Pet Hygiene"],
            "Pharma & Wellness": ["Medicines", "Health Supplements", "First Aid", "Covid Essentials"]
        }
        
        # Create main categories
        for i, cat_name in enumerate(main_categories):
            category = Category(
                name=cat_name.lower().replace(" ", "_").replace("&", "and"),
                display_name=cat_name,
                level=0,
                sort_order=i,
                image_url=f"https://images.example.com/categories/{cat_name.lower().replace(' ', '_')}.jpg"
            )
            self.db.add(category)
            self.categories_data.append(category)
            self.db.flush()  # Get the ID
            
            # Create subcategories
            for j, subcat_name in enumerate(subcategories.get(cat_name, [])):
                subcategory = Category(
                    name=subcat_name.lower().replace(" ", "_").replace("&", "and"),
                    display_name=subcat_name,
                    parent_id=category.id,
                    level=1,
                    sort_order=j,
                    image_url=f"https://images.example.com/subcategories/{subcat_name.lower().replace(' ', '_')}.jpg"
                )
                self.db.add(subcategory)
                self.categories_data.append(subcategory)
    
    def generate_brands(self):
        """Generate brand data"""
        brands_info = [
            ("amul", "Amul", "India", True),
            ("nestle", "Nestle", "Switzerland", True),
            ("britannia", "Britannia", "India", True),
            ("tata", "Tata", "India", True),
            ("mother_dairy", "Mother Dairy", "India", False),
            ("haldiram", "Haldiram", "India", False),
            ("coca_cola", "Coca Cola", "USA", True),
            ("pepsi", "PepsiCo", "USA", True),
            ("unilever", "Unilever", "Netherlands", True),
            ("procter_gamble", "Procter & Gamble", "USA", True),
            ("fortune", "Fortune", "India", False),
            ("saffola", "Saffola", "India", False),
            ("maggi", "Maggi", "Switzerland", True),
            ("kissan", "Kissan", "India", False),
            ("surf_excel", "Surf Excel", "Netherlands", True),
            ("vim", "Vim", "Netherlands", False),
            ("colgate", "Colgate", "USA", True),
            ("oral_b", "Oral-B", "USA", True),
            ("johnson", "Johnson & Johnson", "USA", True),
            ("himalaya", "Himalaya", "India", False)
        ]
        
        for name, display_name, country, is_premium in brands_info:
            brand = Brand(
                name=name,
                display_name=display_name,
                country_of_origin=country,
                is_premium=is_premium,
                logo_url=f"https://logos.example.com/{name}.png",
                website_url=f"https://{name}.com"
            )
            self.db.add(brand)
            self.brands_data.append(brand)
    
    def generate_products(self):
        """Generate product data"""
        # Flush to get category and brand IDs
        self.db.flush()
        
        product_templates = [
            # Fruits & Vegetables
            ("Banana", "fresh_fruits", "Fresh yellow bananas", "piece", True, False, 7, "room_temperature"),
            ("Apple", "fresh_fruits", "Fresh red apples", "kg", True, False, 10, "refrigerated"),
            ("Onion", "fresh_vegetables", "Fresh red onions", "kg", False, True, 30, "room_temperature"),
            ("Potato", "fresh_vegetables", "Fresh potatoes", "kg", False, True, 45, "cool_dry_place"),
            ("Tomato", "fresh_vegetables", "Fresh tomatoes", "kg", False, True, 7, "room_temperature"),
            ("Spinach", "fresh_vegetables", "Fresh spinach leaves", "bunch", True, True, 3, "refrigerated"),
            
            # Dairy & Eggs
            ("Milk", "milk", "Fresh cow milk", "liter", False, True, 2, "refrigerated"),
            ("Curd", "yogurt", "Fresh curd", "gm", False, True, 5, "refrigerated"),
            ("Paneer", "cheese", "Fresh paneer", "gm", False, True, 7, "refrigerated"),
            ("Eggs", "eggs", "Fresh chicken eggs", "piece", False, True, 15, "refrigerated"),
            ("Butter", "butter_and_ghee", "Fresh butter", "gm", False, True, 30, "refrigerated"),
            
            # Snacks & Branded Foods
            ("Lay's Chips", "chips_and_namkeen", "Potato chips", "gm", False, False, 180, "room_temperature"),
            ("Parle-G Biscuits", "biscuits", "Glucose biscuits", "gm", False, False, 365, "room_temperature"),
            ("Maggi Noodles", "ready_to_cook", "Instant noodles", "gm", False, False, 365, "room_temperature"),
            ("Cornflakes", "cereals", "Breakfast cereal", "gm", False, False, 365, "room_temperature"),
            
            # Beverages
            ("Coca Cola", "soft_drinks", "Carbonated soft drink", "ml", False, False, 365, "room_temperature"),
            ("Orange Juice", "juices", "Fresh orange juice", "ml", False, True, 7, "refrigerated"),
            ("Tea Bags", "tea_and_coffee", "Black tea bags", "piece", False, False, 730, "room_temperature"),
            ("Coffee Powder", "tea_and_coffee", "Instant coffee", "gm", False, False, 365, "room_temperature"),
            
            # Personal Care
            ("Shampoo", "hair_care", "Hair shampoo", "ml", False, False, 1095, "room_temperature"),
            ("Soap", "bath_and_body", "Bathing soap", "gm", False, False, 1095, "room_temperature"),
            ("Toothpaste", "oral_care", "Dental toothpaste", "gm", False, False, 730, "room_temperature"),
            ("Face Wash", "skin_care", "Facial cleanser", "ml", False, False, 730, "room_temperature"),
            
            # Household Items
            ("Dish Soap", "cleaning_supplies", "Dishwashing liquid", "ml", False, False, 730, "room_temperature"),
            ("Detergent", "cleaning_supplies", "Laundry detergent", "kg", False, False, 1095, "room_temperature"),
            ("Toilet Paper", "household_items", "Tissue paper rolls", "piece", False, False, 1095, "room_temperature")
        ]
        
        categories_dict = {cat.name: cat.id for cat in self.categories_data}
        brands_dict = {brand.name: brand.id for brand in self.brands_data}
        
        for i, (name, category_name, desc, unit, is_organic, is_fresh, shelf_life, storage) in enumerate(product_templates):
            # Generate multiple variants with different brands
            for j in range(3):  # 3 variants per product template
                brand_name = random.choice(list(brands_dict.keys()))
                product_name = f"{name}" if j == 0 else f"{name} - {random.choice(['Premium', 'Organic', 'Fresh', 'Special'])}"
                
                product = Product(
                    sku=f"SKU{(i*3+j+1):06d}",
                    name=product_name,
                    description=desc,
                    category_id=categories_dict.get(category_name, 1),
                    brand_id=brands_dict.get(brand_name, 1),
                    base_unit=unit,
                    weight=random.uniform(0.1, 5.0) if unit in ["kg", "gm"] else None,
                    volume=random.uniform(0.1, 2.0) if unit in ["liter", "ml"] else None,
                    is_organic=is_organic or random.choice([True, False]) if random.random() < 0.3 else False,
                    is_fresh=is_fresh,
                    shelf_life_days=shelf_life,
                    storage_temperature=storage,
                    barcode=fake.ean13(),
                    nutritional_info=json.dumps({
                        "calories": random.randint(50, 500),
                        "protein": random.uniform(1, 20),
                        "carbs": random.uniform(5, 60),
                        "fat": random.uniform(0, 25)
                    }) if category_name in ["fresh_fruits", "fresh_vegetables", "milk", "cereals"] else None,
                    image_urls=json.dumps([
                        f"https://images.example.com/products/{name.lower().replace(' ', '_')}_1.jpg",
                        f"https://images.example.com/products/{name.lower().replace(' ', '_')}_2.jpg"
                    ]),
                    tags=json.dumps(["popular", "bestseller"] if random.random() < 0.3 else [])
                )
                self.db.add(product)
                self.products_data.append(product)
    
    def generate_product_variants(self):
        """Generate product variants"""
        self.db.flush()
        
        variant_templates = {
            "kg": [("500g", 0.5, "gm"), ("1kg", 1.0, "kg"), ("2kg", 2.0, "kg")],
            "liter": [("500ml", 0.5, "ml"), ("1L", 1.0, "liter"), ("2L", 2.0, "liter")],
            "gm": [("200g", 200, "gm"), ("500g", 500, "gm"), ("1kg", 1000, "gm")],
            "ml": [("250ml", 250, "ml"), ("500ml", 500, "ml"), ("1L", 1000, "ml")],
            "piece": [("1 pc", 1, "piece"), ("6 pcs", 6, "piece"), ("12 pcs", 12, "piece")]
        }
        
        for product in self.products_data:
            if product.base_unit in variant_templates:
                variants = variant_templates[product.base_unit]
                for i, (variant_name, value, unit) in enumerate(variants):
                    variant = ProductVariant(
                        product_id=product.id,
                        variant_name=variant_name,
                        variant_value=value,
                        variant_unit=unit,
                        is_default=(i == 1)  # Middle variant as default
                    )
                    self.db.add(variant)
    
    def generate_suppliers(self):
        """Generate supplier data"""
        indian_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad", "Ahmedabad"]
        
        for i in range(50):
            city = random.choice(indian_cities)
            supplier = Supplier(
                name=fake.company(),
                contact_email=fake.email(),
                contact_phone=fake.phone_number(),
                address=fake.address(),
                city=city,
                state=fake.state(),
                pincode=fake.postcode(),
                rating=random.uniform(3.0, 5.0),
                is_verified=random.choice([True, False])
            )
            self.db.add(supplier)
    
    def generate_product_prices(self):
        """Generate product prices for all platforms"""
        self.db.flush()
        
        platforms = self.db.query(Platform).all()
        products = self.db.query(Product).all()
        suppliers = self.db.query(Supplier).all()
        
        for product in products:
            base_price = random.uniform(10, 500)
            
            for platform in platforms:
                # Platform-specific pricing strategy
                price_multiplier = {
                    "blinkit": random.uniform(0.95, 1.05),
                    "zepto": random.uniform(0.90, 1.00),
                    "instamart": random.uniform(0.98, 1.08),
                    "bigbasket_now": random.uniform(0.85, 0.95),
                    "amazon_fresh": random.uniform(0.80, 0.90)
                }.get(platform.name, random.uniform(0.90, 1.10))
                
                current_price = base_price * price_multiplier
                original_price = current_price * random.uniform(1.0, 1.3)
                discount_percentage = ((original_price - current_price) / original_price) * 100
                
                price = ProductPrice(
                    product_id=product.id,
                    platform_id=platform.id,
                    supplier_id=random.choice(suppliers).id if suppliers else None,
                    current_price=round(current_price, 2),
                    original_price=round(original_price, 2),
                    discount_percentage=round(discount_percentage, 2),
                    discount_amount=round(original_price - current_price, 2),
                    is_available=random.choice([True, True, True, False]),  # 75% availability
                    stock_quantity=random.randint(0, 100),
                    min_order_quantity=random.choice([1, 2, 5]),
                    max_order_quantity=random.randint(50, 200),
                    delivery_time_hours=random.choice([1, 2, 4, 6, 24])
                )
                self.db.add(price)
    
    def generate_promotions(self):
        """Generate promotional offers"""
        platforms = self.db.query(Platform).all()
        
        promotion_types = ["percentage", "fixed_amount", "bogo", "combo"]
        
        for platform in platforms:
            for i in range(random.randint(5, 15)):
                promo_type = random.choice(promotion_types)
                start_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                end_date = start_date + timedelta(days=random.randint(7, 60))
                
                promotion = Promotion(
                    platform_id=platform.id,
                    name=fake.catch_phrase(),
                    description=fake.text(max_nb_chars=200),
                    promotion_type=promo_type,
                    discount_value=random.uniform(5, 50) if promo_type == "percentage" else random.uniform(10, 100),
                    min_order_value=random.choice([0, 99, 199, 299, 499]),
                    max_discount_amount=random.uniform(50, 200) if promo_type == "percentage" else None,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=start_date <= datetime.utcnow() <= end_date,
                    usage_limit=random.randint(100, 10000),
                    usage_count=random.randint(0, 1000),
                    applicable_categories=json.dumps([random.randint(1, 10) for _ in range(random.randint(1, 3))])
                )
                self.db.add(promotion)
    
    def generate_delivery_zones(self):
        """Generate delivery zones"""
        platforms = self.db.query(Platform).all()
        indian_cities = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad", "Ahmedabad"]
        
        for platform in platforms:
            for city in indian_cities:
                for zone_num in range(random.randint(2, 5)):
                    zone = DeliveryZone(
                        platform_id=platform.id,
                        zone_name=f"{city} Zone {zone_num + 1}",
                        city=city,
                        state=fake.state(),
                        pincodes=json.dumps([fake.postcode() for _ in range(random.randint(5, 15))]),
                        delivery_fee=random.choice([0, 19, 29, 39, 49]),
                        free_delivery_threshold=random.choice([199, 299, 399, 499]),
                        average_delivery_time=random.randint(15, 120)
                    )
                    self.db.add(zone)
    
    def generate_platform_availability(self):
        """Generate platform availability data"""
        self.db.flush()
        
        platforms = self.db.query(Platform).all()
        products = self.db.query(Product).all()
        zones = self.db.query(DeliveryZone).all()
        
        for platform in platforms:
            platform_zones = [z for z in zones if z.platform_id == platform.id]
            
            for zone in platform_zones[:3]:  # Limit to reduce data size
                for product in random.sample(products, min(len(products), 50)):
                    availability = PlatformAvailability(
                        platform_id=platform.id,
                        delivery_zone_id=zone.id,
                        product_id=product.id,
                        is_available=random.choice([True, True, True, False]),
                        estimated_delivery_time=random.randint(30, 180)
                    )
                    self.db.add(availability)
    
    def generate_users(self):
        """Generate user data"""
        for i in range(100):
            user = User(
                email=fake.email(),
                phone=fake.phone_number(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=65),
                gender=random.choice(["male", "female", "other"]),
                preferred_platforms=json.dumps(random.sample(Config.PLATFORMS, random.randint(2, 5))),
                preferred_categories=json.dumps([random.randint(1, 20) for _ in range(random.randint(3, 8))]),
                budget_range=random.choice(["low", "medium", "high", "premium"]),
                dietary_preferences=json.dumps(random.sample(["vegetarian", "vegan", "organic", "gluten_free"], random.randint(0, 2))),
                is_premium=random.choice([True, False]),
                total_orders=random.randint(0, 200),
                total_spent=random.uniform(0, 50000),
                last_active=fake.date_time_between(start_date="-30d", end_date="now")
            )
            self.db.add(user)
    
    def generate_user_addresses(self):
        """Generate user addresses"""
        self.db.flush()
        users = self.db.query(User).all()
        
        for user in users:
            for i in range(random.randint(1, 3)):
                address = UserAddress(
                    user_id=user.id,
                    address_type=random.choice(["home", "office", "other"]),
                    address_line1=fake.street_address(),
                    address_line2=fake.secondary_address() if random.random() < 0.3 else None,
                    city=fake.city(),
                    state=fake.state(),
                    pincode=fake.postcode(),
                    landmark=fake.street_name() if random.random() < 0.5 else None,
                    latitude=fake.latitude(),
                    longitude=fake.longitude(),
                    is_default=(i == 0)
                )
                self.db.add(address)
    
    def generate_product_popularity(self):
        """Generate product popularity data"""
        self.db.flush()
        products = self.db.query(Product).all()
        platforms = self.db.query(Platform).all()
        
        for product in products:
            for platform in platforms:
                if random.random() < 0.7:  # 70% chance of having popularity data
                    popularity = ProductPopularity(
                        product_id=product.id,
                        platform_id=platform.id,
                        search_count=random.randint(0, 1000),
                        view_count=random.randint(0, 5000),
                        comparison_count=random.randint(0, 500),
                        popularity_score=random.uniform(0, 100),
                        date=fake.date_time_between(start_date="-30d", end_date="now")
                    )
                    self.db.add(popularity)
    
    def generate_price_history(self):
        """Generate price history data"""
        self.db.flush()
        product_prices = self.db.query(ProductPrice).all()
        
        for price in random.sample(product_prices, min(len(product_prices), 200)):
            # Generate 3-10 price changes
            for i in range(random.randint(3, 10)):
                old_price = price.current_price * random.uniform(0.8, 1.2)
                new_price = price.current_price * random.uniform(0.8, 1.2)
                change_percentage = ((new_price - old_price) / old_price) * 100
                
                history = PriceHistory(
                    product_price_id=price.id,
                    old_price=round(old_price, 2),
                    new_price=round(new_price, 2),
                    change_percentage=round(change_percentage, 2),
                    reason=random.choice(["promotion", "stock_change", "market_update", "competitor_pricing"]),
                    changed_at=fake.date_time_between(start_date="-60d", end_date="now")
                )
                self.db.add(history)
    
    def generate_market_trends(self):
        """Generate market trend data"""
        self.db.flush()
        categories = self.db.query(Category).all()
        platforms = self.db.query(Platform).all()
        
        for category in categories:
            for platform in platforms:
                for period in ["daily", "weekly", "monthly"]:
                    trend = MarketTrend(
                        category_id=category.id,
                        platform_id=platform.id,
                        trend_period=period,
                        average_price=random.uniform(50, 500),
                        price_change_percentage=random.uniform(-20, 20),
                        total_products=random.randint(10, 100),
                        products_on_discount=random.randint(1, 50),
                        average_discount_percentage=random.uniform(5, 30),
                        trend_date=fake.date_time_between(start_date="-30d", end_date="now")
                    )
                    self.db.add(trend)
    
    def generate_inventory_levels(self):
        """Generate inventory level data"""
        self.db.flush()
        products = self.db.query(Product).all()
        platforms = self.db.query(Platform).all()
        
        for product in products:
            for platform in platforms:
                current_stock = random.randint(0, 500)
                reserved_stock = random.randint(0, min(current_stock, 50))
                available_stock = current_stock - reserved_stock
                
                stock_status = "out_of_stock" if current_stock == 0 else \
                              "low_stock" if current_stock < 10 else "in_stock"
                
                inventory = InventoryLevel(
                    product_id=product.id,
                    platform_id=platform.id,
                    current_stock=current_stock,
                    reserved_stock=reserved_stock,
                    available_stock=available_stock,
                    reorder_level=random.randint(5, 20),
                    max_stock_level=random.randint(200, 1000),
                    last_restocked=fake.date_time_between(start_date="-7d", end_date="now"),
                    next_restock_date=fake.date_time_between(start_date="now", end_date="+7d"),
                    stock_status=stock_status
                )
                self.db.add(inventory)
    
    def generate_product_reviews(self):
        """Generate product reviews"""
        self.db.flush()
        products = self.db.query(Product).all()
        platforms = self.db.query(Platform).all()
        users = self.db.query(User).all()
        
        for product in random.sample(products, min(len(products), 100)):
            for platform in random.sample(platforms, random.randint(1, 3)):
                for i in range(random.randint(0, 10)):
                    review = ProductReview(
                        product_id=product.id,
                        platform_id=platform.id,
                        user_id=random.choice(users).id if users else None,
                        rating=random.uniform(1.0, 5.0),
                        review_text=fake.text(max_nb_chars=200),
                        is_verified_purchase=random.choice([True, False]),
                        helpful_count=random.randint(0, 50),
                        created_at=fake.date_time_between(start_date="-90d", end_date="now")
                    )
                    self.db.add(review)
    
    def generate_platform_ratings(self):
        """Generate platform ratings"""
        self.db.flush()
        platforms = self.db.query(Platform).all()
        users = self.db.query(User).all()
        
        for platform in platforms:
            for i in range(random.randint(50, 200)):
                delivery_rating = random.uniform(2.0, 5.0)
                app_rating = random.uniform(2.0, 5.0)
                service_rating = random.uniform(2.0, 5.0)
                overall_rating = (delivery_rating + app_rating + service_rating) / 3
                
                rating = PlatformRating(
                    platform_id=platform.id,
                    user_id=random.choice(users).id if users else None,
                    delivery_rating=round(delivery_rating, 1),
                    app_rating=round(app_rating, 1),
                    customer_service_rating=round(service_rating, 1),
                    overall_rating=round(overall_rating, 1),
                    review_text=fake.text(max_nb_chars=300),
                    created_at=fake.date_time_between(start_date="-180d", end_date="now")
                )
                self.db.add(rating)
    
    def generate_competitor_analysis(self):
        """Generate competitor analysis data"""
        self.db.flush()
        products = self.db.query(Product).all()
        platforms = self.db.query(Platform).all()
        
        for product in random.sample(products, min(len(products), 50)):
            platform_pairs = [(platforms[i], platforms[j]) 
                            for i in range(len(platforms)) 
                            for j in range(i+1, len(platforms))]
            
            for platform1, platform2 in random.sample(platform_pairs, min(len(platform_pairs), 5)):
                platform1_price = random.uniform(50, 500)
                platform2_price = random.uniform(50, 500)
                price_difference = abs(platform1_price - platform2_price)
                cheaper_platform = platform1 if platform1_price < platform2_price else platform2
                
                analysis = CompetitorAnalysis(
                    product_id=product.id,
                    platform1_id=platform1.id,
                    platform2_id=platform2.id,
                    price_difference=round(price_difference, 2),
                    platform1_price=round(platform1_price, 2),
                    platform2_price=round(platform2_price, 2),
                    cheaper_platform_id=cheaper_platform.id,
                    analysis_date=fake.date_time_between(start_date="-7d", end_date="now")
                )
                self.db.add(analysis)

def initialize_database():
    """Initialize database with sample data"""
    generator = DataGenerator()
    generator.generate_all_data()
    print("Database initialized with sample data successfully!")

if __name__ == "__main__":
    initialize_database()
