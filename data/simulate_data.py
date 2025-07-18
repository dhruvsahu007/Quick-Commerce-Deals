import asyncio
import random
import time
from datetime import datetime, timedelta
from database.connection import get_db_session
from database.models import ProductPrice, PriceHistory, InventoryLevel, Promotion
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class RealTimeDataSimulator:
    """Simulate real-time price updates and inventory changes"""
    
    def __init__(self):
        self.db = get_db_session()
        self.is_running = False
        self.update_interval = Config.SIMULATION_INTERVAL
        
    async def start_simulation(self):
        """Start real-time data simulation"""
        self.is_running = True
        logger.info("Starting real-time data simulation...")
        
        while self.is_running:
            try:
                await self.simulate_price_updates()
                await self.simulate_inventory_changes()
                await self.simulate_promotional_updates()
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.is_running = False
        logger.info("Stopping real-time data simulation...")
    
    async def simulate_price_updates(self):
        """Simulate realistic price changes"""
        try:
            # Get a random sample of product prices
            product_prices = self.db.query(ProductPrice).limit(50).all()
            
            updated_count = 0
            for price in random.sample(product_prices, min(10, len(product_prices))):
                # Simulate price change with realistic patterns
                old_price = price.current_price
                
                # Different change patterns based on time and product type
                change_factor = self._calculate_price_change_factor()
                new_price = max(old_price * change_factor, 1.0)  # Minimum price of ₹1
                
                # Update price if change is significant enough (>1%)
                price_change_percent = abs((new_price - old_price) / old_price) * 100
                if price_change_percent > 1:
                    # Create price history record
                    history = PriceHistory(
                        product_price_id=price.id,
                        old_price=old_price,
                        new_price=new_price,
                        change_percentage=((new_price - old_price) / old_price) * 100,
                        reason=self._get_price_change_reason(change_factor),
                        changed_at=datetime.utcnow()
                    )
                    
                    # Update current price
                    price.current_price = round(new_price, 2)
                    price.discount_percentage = max(0, ((price.original_price - price.current_price) / price.original_price) * 100)
                    price.discount_amount = max(0, price.original_price - price.current_price)
                    price.last_updated = datetime.utcnow()
                    
                    self.db.add(history)
                    updated_count += 1
            
            self.db.commit()
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} product prices")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Price update simulation failed: {e}")
        finally:
            self.db.close()
            self.db = get_db_session()  # Get fresh session
    
    def _calculate_price_change_factor(self) -> float:
        """Calculate realistic price change factor"""
        current_hour = datetime.now().hour
        
        # Price patterns based on time of day
        if 6 <= current_hour <= 10:  # Morning rush
            base_factor = random.uniform(1.02, 1.08)  # Slight increase
        elif 17 <= current_hour <= 21:  # Evening rush  
            base_factor = random.uniform(1.01, 1.05)  # Moderate increase
        elif 22 <= current_hour or current_hour <= 5:  # Night/early morning
            base_factor = random.uniform(0.95, 1.02)  # Possible discounts
        else:  # Regular hours
            base_factor = random.uniform(0.98, 1.03)  # Minor fluctuations
        
        # Add random market volatility
        volatility = random.uniform(0.95, 1.05)
        
        return base_factor * volatility
    
    def _get_price_change_reason(self, change_factor: float) -> str:
        """Get reason for price change based on factor"""
        if change_factor > 1.05:
            return random.choice(["high_demand", "low_stock", "market_increase"])
        elif change_factor < 0.95:
            return random.choice(["promotion", "excess_stock", "competition"])
        else:
            return "market_update"
    
    async def simulate_inventory_changes(self):
        """Simulate inventory level changes"""
        try:
            # Get inventory records
            inventory_records = self.db.query(InventoryLevel).limit(30).all()
            
            updated_count = 0
            for inventory in random.sample(inventory_records, min(8, len(inventory_records))):
                # Simulate stock changes
                old_stock = inventory.current_stock
                
                # Random stock change (-20 to +50 items)
                stock_change = random.randint(-20, 50)
                new_stock = max(0, old_stock + stock_change)
                
                # Update inventory
                inventory.current_stock = new_stock
                inventory.available_stock = max(0, new_stock - inventory.reserved_stock)
                
                # Update stock status
                if new_stock == 0:
                    inventory.stock_status = "out_of_stock"
                elif new_stock <= inventory.reorder_level:
                    inventory.stock_status = "low_stock"
                else:
                    inventory.stock_status = "in_stock"
                
                inventory.updated_at = datetime.utcnow()
                
                # Update product availability
                product_price = self.db.query(ProductPrice).filter(
                    ProductPrice.product_id == inventory.product_id,
                    ProductPrice.platform_id == inventory.platform_id
                ).first()
                
                if product_price:
                    product_price.is_available = new_stock > 0
                    product_price.stock_quantity = new_stock
                    product_price.last_updated = datetime.utcnow()
                
                updated_count += 1
            
            self.db.commit()
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} inventory records")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Inventory update simulation failed: {e}")
    
    async def simulate_promotional_updates(self):
        """Simulate promotional offers changes"""
        try:
            # Randomly activate/deactivate promotions
            promotions = self.db.query(Promotion).limit(20).all()
            
            updated_count = 0
            for promotion in random.sample(promotions, min(3, len(promotions))):
                current_time = datetime.utcnow()
                
                # Randomly toggle promotion status
                if random.random() < 0.3:  # 30% chance of status change
                    if promotion.is_active and current_time > promotion.end_date:
                        promotion.is_active = False
                        updated_count += 1
                    elif not promotion.is_active and promotion.start_date <= current_time <= promotion.end_date:
                        promotion.is_active = True
                        updated_count += 1
            
            # Create new flash promotions occasionally
            if random.random() < 0.1:  # 10% chance
                self._create_flash_promotion()
                updated_count += 1
            
            self.db.commit()
            
            if updated_count > 0:
                logger.info(f"Updated {updated_count} promotions")
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Promotion update simulation failed: {e}")
    
    def _create_flash_promotion(self):
        """Create a flash promotion"""
        from database.models import Platform
        
        platforms = self.db.query(Platform).all()
        if not platforms:
            return
        
        platform = random.choice(platforms)
        
        promotion = Promotion(
            platform_id=platform.id,
            name=f"Flash Sale - {random.choice(['Super Saver', 'Lightning Deal', 'Quick Grab'])}",
            description="Limited time flash promotion",
            promotion_type="percentage",
            discount_value=random.uniform(15, 40),
            min_order_value=random.choice([0, 99, 199]),
            max_discount_amount=random.uniform(50, 200),
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(hours=random.randint(2, 8)),
            is_active=True,
            usage_limit=random.randint(50, 500)
        )
        
        self.db.add(promotion)
        logger.info(f"Created flash promotion: {promotion.name}")

class MarketDataGenerator:
    """Generate additional market data and insights"""
    
    def __init__(self):
        self.db = get_db_session()
    
    def generate_competitor_insights(self):
        """Generate competitive analysis data"""
        from database.models import Product, ProductPrice, Platform, CompetitorAnalysis
        
        try:
            # Get products that are available on multiple platforms
            products_with_multiple_platforms = self.db.query(Product.id).join(
                ProductPrice
            ).group_by(Product.id).having(
                self.db.query(ProductPrice.platform_id).filter(
                    ProductPrice.product_id == Product.id
                ).count() > 1
            ).limit(20).all()
            
            for (product_id,) in products_with_multiple_platforms:
                product_prices = self.db.query(ProductPrice).filter(
                    ProductPrice.product_id == product_id,
                    ProductPrice.is_available == True
                ).all()
                
                # Compare all platform pairs for this product
                for i in range(len(product_prices)):
                    for j in range(i + 1, len(product_prices)):
                        price1 = product_prices[i]
                        price2 = product_prices[j]
                        
                        # Create or update competitor analysis
                        existing_analysis = self.db.query(CompetitorAnalysis).filter(
                            CompetitorAnalysis.product_id == product_id,
                            CompetitorAnalysis.platform1_id == price1.platform_id,
                            CompetitorAnalysis.platform2_id == price2.platform_id
                        ).first()
                        
                        if existing_analysis:
                            # Update existing analysis
                            existing_analysis.platform1_price = price1.current_price
                            existing_analysis.platform2_price = price2.current_price
                            existing_analysis.price_difference = abs(price1.current_price - price2.current_price)
                            existing_analysis.cheaper_platform_id = price1.platform_id if price1.current_price < price2.current_price else price2.platform_id
                            existing_analysis.analysis_date = datetime.utcnow()
                        else:
                            # Create new analysis
                            analysis = CompetitorAnalysis(
                                product_id=product_id,
                                platform1_id=price1.platform_id,
                                platform2_id=price2.platform_id,
                                price_difference=abs(price1.current_price - price2.current_price),
                                platform1_price=price1.current_price,
                                platform2_price=price2.current_price,
                                cheaper_platform_id=price1.platform_id if price1.current_price < price2.current_price else price2.platform_id,
                                analysis_date=datetime.utcnow()
                            )
                            self.db.add(analysis)
            
            self.db.commit()
            logger.info("Generated competitor insights")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to generate competitor insights: {e}")
        finally:
            self.db.close()
    
    def update_popularity_metrics(self):
        """Update product popularity metrics"""
        from database.models import Product, ProductPopularity, Platform
        
        try:
            products = self.db.query(Product).limit(50).all()
            platforms = self.db.query(Platform).all()
            
            for product in random.sample(products, min(20, len(products))):
                for platform in random.sample(platforms, min(3, len(platforms))):
                    # Get or create popularity record
                    popularity = self.db.query(ProductPopularity).filter(
                        ProductPopularity.product_id == product.id,
                        ProductPopularity.platform_id == platform.id,
                        ProductPopularity.date >= datetime.utcnow().date()
                    ).first()
                    
                    if popularity:
                        # Update existing record
                        popularity.search_count += random.randint(0, 10)
                        popularity.view_count += random.randint(0, 50)
                        popularity.comparison_count += random.randint(0, 5)
                    else:
                        # Create new record
                        popularity = ProductPopularity(
                            product_id=product.id,
                            platform_id=platform.id,
                            search_count=random.randint(0, 20),
                            view_count=random.randint(0, 100),
                            comparison_count=random.randint(0, 10),
                            date=datetime.utcnow()
                        )
                        self.db.add(popularity)
                    
                    # Calculate popularity score
                    if popularity:
                        popularity.popularity_score = (
                            popularity.search_count * 3 +
                            popularity.view_count +
                            popularity.comparison_count * 5
                        ) / 10
            
            self.db.commit()
            logger.info("Updated popularity metrics")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update popularity metrics: {e}")
        finally:
            self.db.close()

async def run_data_simulation():
    """Run the data simulation"""
    simulator = RealTimeDataSimulator()
    market_generator = MarketDataGenerator()
    
    try:
        # Start real-time simulation
        simulation_task = asyncio.create_task(simulator.start_simulation())
        
        # Periodically generate market insights
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            market_generator.generate_competitor_insights()
            market_generator.update_popularity_metrics()
            
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
        simulator.stop_simulation()
        await simulation_task

if __name__ == "__main__":
    asyncio.run(run_data_simulation())
