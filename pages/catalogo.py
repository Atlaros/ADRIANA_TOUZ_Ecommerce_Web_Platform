import streamlit as st
import stripe
import os
from datetime import datetime, timedelta
import time
from collections import Counter
import random

if 'login' not in st.session_state:
    st.switch_page('app.py')

# CSS personalizado para el diseño de lujo
with open("estilos/css_catalogo.html", "r") as file:
    html_content = file.read()
st.markdown(html_content, unsafe_allow_html=True)

# Configuración de Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

def simulate_payment_processing():
    """Simula el procesamiento de pago"""
    import time
    with st.spinner('Procesando pago...'):
        time.sleep(2)  # Simular tiempo de procesamiento
    return True

def create_simulated_order(items, user_data):
    """Crea una orden simulada sin usar Stripe"""
    try:
        # Generar un número de orden único
        order_number = f"SIM-{int(time.time())}-{user_data['uid'][:8]}"
        
        # Calcular total
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # Formatear items
        formatted_items = []
        for item in items:
            formatted_items.append({
                'name': item['name'],
                'price': float(item['price']),
                'quantity': int(item['quantity']),
                'image': item.get('image', ''),
                'subtotal': float(item['price']) * int(item['quantity'])
            })
        
        # Crear datos de la orden
        order_data = {
            'order_number': order_number,
            'user_id': user_data['uid'],
            'user_name': user_data['nombre'],
            'user_email': user_data['email'],
            'items': formatted_items,
            'total': float(total),
            'status': 'completed',
            'payment_method': 'simulated',
            'created_at': datetime.now(),
            'currency': 'USD',
            'simulation': True  # Marca para identificar órdenes simuladas
        }
        
        # Guardar en Firestore
        doc_ref = st.session_state.db.collection('orders').add(order_data)
        
        if doc_ref and len(doc_ref) > 1:
            st.success(f"✅ Orden simulada creada: {order_number}")
            return order_number, order_data
        else:
            st.error("❌ Error al crear la orden")
            return None, None
            
    except Exception as e:
        st.error(f"❌ Error en la simulación de compra: {str(e)}")
        return None, None

def process_simulated_checkout_improved():
    """Versión mejorada del checkout simulado con mejor manejo del carrito"""
    if not st.session_state.cart:
        st.error("❌ El carrito está vacío")
        return False
    
    try:
        # 1. Guardar copia del carrito antes de procesar
        cart_backup = st.session_state.cart.copy()
        
        # 2. Simular procesamiento de pago
        with st.spinner('Procesando pago simulado...'):
            time.sleep(2)  # Simular tiempo de procesamiento
        
        # 3. Crear orden
        order_number, order_data = create_simulated_order(
            cart_backup,  # Usar backup por si algo falla
            st.session_state['usuario']
        )
        
        if order_number:
            # 4. Actualizar stock
            update_product_stock(cart_backup)
            
            # 5. Registrar productos para ofertas
            track_user_product_preferences(st.session_state['usuario']['uid'], cart_backup)
            
            # 6. LIMPIEZA MEJORADA DEL CARRITO
            success_cleanup = clear_cart_after_purchase()
            
            if not success_cleanup:
                st.warning("⚠️ Problemas con limpieza automática, ejecutando limpieza de emergencia...")
                emergency_cart_cleanup()
            
            # 7. Verificar que esté vacío
            verify_cart_empty()
            
            # 8. Forzar actualización visual
            force_cart_refresh()
            
            # 9. Mostrar confirmación
            show_purchase_confirmation(order_number, order_data)
            
            # 10. Mostrar globos de celebración
            st.balloons()
            
            return True
        else:
            st.error("❌ Error al crear la orden")
            return False
            
    except Exception as e:
        st.error(f"❌ Error en checkout simulado: {str(e)}")
        
        # En caso de error, intentar limpieza de emergencia
        st.warning("🚨 Ejecutando procedimiento de emergencia...")
        emergency_cart_cleanup()
        
        return False

def clear_cart_after_purchase():
    """Limpia el carrito después de una compra exitosa"""
    try:
        # 1. Limpiar session_state
        st.session_state.cart = []
        
        # 2. Limpiar en Firebase
        if 'usuario' in st.session_state and st.session_state.usuario:
            user_id = st.session_state.usuario['uid']
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            
            # Eliminar documento del carrito o vaciarlo
            cart_doc = cart_ref.get()
            if cart_doc.exists:
                cart_ref.delete()  # Eliminar completamente
                st.success("✅ Carrito limpiado tras compra exitosa")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al limpiar carrito: {str(e)}")
        return False

def show_purchase_confirmation(order_number, order_data):
    """Muestra confirmación de compra"""
    st.balloons()
    st.success("🎉 ¡Compra realizada con éxito!")
    
    with st.expander("📋 Detalles de tu orden", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Número de orden:** {order_number}")
            st.write(f"**Cliente:** {order_data['user_name']}")
            st.write(f"**Email:** {order_data['user_email']}")
            st.write(f"**Fecha:** {order_data['created_at'].strftime('%d/%m/%Y %H:%M')}")
        
        with col2:
            st.write(f"**Total:** ${order_data['total']:.2f}")
            st.write(f"**Método de pago:** Simulado")
            st.write(f"**Estado:** ✅ Completado")
        
        st.write("**Productos comprados:**")
        for item in order_data['items']:
            st.write(f"• {item['name']} - Cantidad: {item['quantity']} - ${item['subtotal']:.2f}")

# ========== SISTEMA DE OFERTAS BASADO EN PREFERENCIAS ==========

def track_user_product_preferences(user_id, cart_items):
    """Registra las preferencias del usuario basadas en productos del carrito"""
    try:
        # Obtener categorías de los productos en el carrito
        categories = []
        product_names = []
        
        for item in cart_items:
            product_names.append(item['name'])
            # Buscar la categoría del producto
            products_ref = st.session_state.db.collection('products')
            query = products_ref.where('name', '==', item['name'])
            docs = list(query.stream())
            
            for doc in docs:
                product_data = doc.to_dict()
                category = product_data.get('category', 'general')
                categories.extend([category] * item['quantity'])  # Peso por cantidad
        
        # Guardar/actualizar preferencias del usuario
        preferences_ref = st.session_state.db.collection('user_preferences').document(user_id)
        preferences_doc = preferences_ref.get()
        
        if preferences_doc.exists:
            # Actualizar preferencias existentes
            current_prefs = preferences_doc.to_dict()
            current_categories = current_prefs.get('preferred_categories', [])
            current_products = current_prefs.get('preferred_products', [])
            
            # Agregar nuevas preferencias
            current_categories.extend(categories)
            current_products.extend(product_names)
            
            preferences_ref.update({
                'preferred_categories': current_categories,
                'preferred_products': current_products,
                'last_updated': datetime.now()
            })
        else:
            # Crear nuevas preferencias
            preferences_ref.set({
                'user_id': user_id,
                'preferred_categories': categories,
                'preferred_products': product_names,
                'created_at': datetime.now(),
                'last_updated': datetime.now()
            })
        
        st.success("✅ Preferencias actualizadas para ofertas personalizadas")
        
    except Exception as e:
        st.error(f"❌ Error al registrar preferencias: {str(e)}")

def get_user_preferences(user_id):
    """Obtiene las preferencias del usuario"""
    try:
        preferences_ref = st.session_state.db.collection('user_preferences').document(user_id)
        preferences_doc = preferences_ref.get()
        
        if preferences_doc.exists:
            return preferences_doc.to_dict()
        else:
            return None
            
    except Exception as e:
        st.error(f"❌ Error al obtener preferencias: {str(e)}")
        return None

def generate_personalized_offers(user_id, products):
    """Genera ofertas personalizadas basadas en las preferencias del usuario"""
    try:
        # Obtener preferencias del usuario
        preferences = get_user_preferences(user_id)
        
        if not preferences:
            # Si no hay preferencias, mostrar ofertas aleatorias
            return generate_random_offers(products)
        
        # Contar categorías más frecuentes
        categories = preferences.get('preferred_categories', [])
        category_counts = Counter(categories)
        top_category = category_counts.most_common(1)[0][0] if category_counts else None
        
        # Contar productos más frecuentes
        product_names = preferences.get('preferred_products', [])
        product_counts = Counter(product_names)
        
        offers = []
        
        # Generar ofertas basadas en categoría preferida
        if top_category:
            category_products = [p for p in products if p.get('category') == top_category]
            for product in category_products[:2]:  # Máximo 2 ofertas por categoría
                discount = random.randint(15, 40)
                offers.append({
                    'product': product,
                    'discount': discount,
                    'reason': f'¡Te encanta la categoría {top_category.title()}!'
                })
        
        # Generar ofertas basadas en productos similares
        if product_counts:
            most_liked_product = product_counts.most_common(1)[0][0]
            # Buscar productos de la misma categoría que el más gustado
            for product in products:
                if product['name'] != most_liked_product and len(offers) < 3:
                    # Buscar categoría del producto más gustado
                    for p in products:
                        if p['name'] == most_liked_product:
                            liked_category = p.get('category')
                            if product.get('category') == liked_category:
                                discount = random.randint(10, 35)
                                offers.append({
                                    'product': product,
                                    'discount': discount,
                                    'reason': f'Similar a {most_liked_product} que te gusta'
                                })
                            break
        
        return offers[:3]  # Máximo 3 ofertas
        
    except Exception as e:
        st.error(f"❌ Error al generar ofertas: {str(e)}")
        return generate_random_offers(products)

def generate_random_offers(products):
    """Genera ofertas aleatorias como fallback"""
    offers = []
    selected_products = random.sample(products, min(3, len(products)))
    
    for product in selected_products:
        discount = random.randint(10, 30)
        offers.append({
            'product': product,
            'discount': discount,
            'reason': '¡Oferta especial del día!'
        })
    
    return offers

def display_personalized_offers(user_id, products):
    """Muestra las ofertas personalizadas de manera llamativa"""
    offers = generate_personalized_offers(user_id, products)
    
    if offers:
        st.markdown("""
        <div style="background: linear-gradient(45deg, #FF6B6B, #FFE66D); 
                    padding: 20px; border-radius: 15px; margin: 20px 0; 
                    box-shadow: 0 8px 32px rgba(255, 107, 107, 0.3);
                    animation: pulse 2s infinite;">
            <h2 style="color: white; text-align: center; margin: 0; 
                       text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
                🔥 ¡OFERTAS ESPECIALES PARA TI! 🔥
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar ofertas en columnas
        cols = st.columns(len(offers))
        
        for idx, offer in enumerate(offers):
            with cols[idx]:
                product = offer['product']
                discount = offer['discount']
                original_price = product['price']
                discounted_price = original_price * (1 - discount / 100)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                           border-radius: 15px; padding: 15px; margin: 10px 0;
                           box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                           transform: rotate(-1deg); color: white;
                           border: 3px solid #FFD700;">
                    <div style="text-align: center;">
                        <h4 style="margin: 5px 0; color: #FFD700;">🎯 OFERTA PERSONALIZADA</h4>
                        <img src="{product['image']}" style="width: 100%; height: 120px; 
                             object-fit: cover; border-radius: 10px; margin: 8px 0;">
                        <h5 style="margin: 8px 0; color: white;">{product['name']}</h5>
                        <div style="background: #FF4757; color: white; padding: 5px; 
                                   border-radius: 20px; margin: 5px 0; font-weight: bold;">
                            -{discount}% OFF
                        </div>
                        <p style="margin: 5px 0; font-size: 12px; color: #FFE66D;">
                            {offer['reason']}
                        </p>
                        <div style="margin: 8px 0;">
                            <span style="text-decoration: line-through; color: #ff7675;">
                                ${original_price:.2f}
                            </span>
                            <br>
                            <span style="font-size: 18px; font-weight: bold; color: #00b894;">
                                ${discounted_price:.2f}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón de agregar al carrito con precio de oferta
                if st.button(f"🛒 ¡Aprovecha la Oferta!", key=f"offer_{idx}"):
                    # Crear producto con precio de oferta
                    offer_product = product.copy()
                    offer_product['price'] = discounted_price
                    offer_product['name'] = f"{product['name']} (OFERTA -{discount}%)"
                    
                    if add_to_cart_improved(offer_product, st.session_state.usuario['uid']):
                        st.success(f"🎉 ¡Oferta aprovechada! {offer_product['name']} agregado al carrito")
                        st.rerun()

def clear_existing_products():
    """Elimina todos los productos existentes de Firestore"""
    try:
        products_ref = st.session_state.db.collection('products')
        docs = products_ref.stream()
        
        for doc in docs:
            doc.reference.delete()
        
        st.success("Productos existentes eliminados")
        return True
    
    except Exception as e:
        st.error(f"Error al eliminar productos: {str(e)}")
        return False

def force_refresh_products():
    """Fuerza la actualización de productos"""
    try:
        # Eliminar productos existentes
        clear_existing_products()
        
        # Los nuevos productos se crearán automáticamente 
        # cuando get_products() no encuentre productos
        
        st.success("Productos actualizados correctamente")
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al actualizar productos: {str(e)}")

# NUEVA FUNCIÓN: Verificar si Firebase está conectado
def test_firebase_connection():
    """Prueba la conexión a Firebase"""
    try:
        # Intentar leer/escribir en una colección de prueba
        test_ref = st.session_state.db.collection('test')
        test_doc = test_ref.document('connection_test')
        test_doc.set({
            'timestamp': datetime.now(),
            'status': 'connected'
        })
        
        # Leer el documento para confirmar
        doc = test_doc.get()
        if doc.exists:
            # Eliminar el documento de prueba
            test_doc.delete()
            return True
        return False
    except Exception as e:
        st.error(f"Error de conexión a Firebase: {str(e)}")
        return False

# Funciones de Firestore
def get_products():
    """Obtiene productos desde Firestore"""
    try:
        products_ref = st.session_state.db.collection('products')
        docs = products_ref.stream()
        
        products = []
        for doc in docs:
            product = doc.to_dict()
            product['id'] = doc.id
            products.append(product)
        
        # Si no hay productos, crear algunos de ejemplo
        if not products:
            sample_products = [
                {
                    "name": "Vestido Elegante",
                    "price": 89.99,
                    "image": "https://i.imgur.com/TRmtJwn.jpg",
                    "description": "Vestido elegante, perfecto para ocasiones especiales",
                    "category": "vestidos",
                    "stock": 15
                },
                {
                    "name": "Blusa Casual",
                    "price": 45.99,
                    "image": "https://i.imgur.com/NqHc7ri.jpg",
                    "description": "Blusa cómoda y versátil para el día a día",
                    "category": "blusas",
                    "stock": 25
                },
                {
                    "name": "Pantalon palazo",
                    "price": 79.99,
                    "image": "https://i.imgur.com/oS0BYH1.jpg",
                    "description": "pantalón palazo de alta calidad, ideal para combinar",
                    "category": "pantalones",
                    "stock": 20
                },
                {
                    "name": "Blazer",
                    "price": 129.99,
                    "image": "https://i.imgur.com/yCMtdfa.jpg",
                    "description": "Blazer elegante de calidad, ideal para ocasiones especiales",
                    "category": "chaquetas",
                    "stock": 8
                },
                {
                    "name": "Zapatos Elegantes",
                    "price": 95.99,
                    "image": "https://i.imgur.com/uKfw8iR.jpg",
                    "description": "Zapatos elegantes para completar tu look",
                    "category": "zapatos",
                    "stock": 12
                },
                {
                    "name": "Bolso de Mano",
                    "price": 65.99,
                    "image": "https://i.imgur.com/T99kfQS.jpg",
                    "description": "Bolso de mano versátil y elegante para cualquier ocasión",
                    "category": "accesorios",
                    "stock": 18
                }
            ]
            
            # Agregar productos de ejemplo a Firestore
            for product in sample_products:
                st.session_state.db.collection('products').add(product)
            
            return sample_products
        
        return products
    
    except Exception as e:
        st.error(f"Error al obtener productos: {str(e)}")
        return []

# FUNCIÓN CORREGIDA
def add_to_cart(product_id, user_id):
    """Agrega producto al carrito en Firebase"""
    try:
        cart_ref = st.session_state.db.collection('carts').document(user_id)
        cart_doc = cart_ref.get()
        
        if cart_doc.exists:
            cart_data = cart_doc.to_dict()
            items = cart_data.get('items', [])
            
            # Verificar si el producto ya está en el carrito
            product_exists = False
            for item in items:
                if item['product_id'] == product_id:
                    item['quantity'] += 1
                    product_exists = True
                    break
            
            if not product_exists:
                items.append({
                    'product_id': product_id,
                    'quantity': 1,
                    'added_at': datetime.now()
                })
            
            cart_ref.update({'items': items})
        else:
            # CORREGIDO: Usar set() en lugar de document().add()
            cart_ref.set({
                'user_id': user_id,  # Agregar user_id
                'items': [{
                    'product_id': product_id,
                    'quantity': 1,
                    'added_at': datetime.now()
                }],
                'created_at': datetime.now()
            })
        
        return True
    
    except Exception as e:
        st.error(f"Error al agregar al carrito: {str(e)}")
        return False

def get_cart(user_id):
    """Obtiene el carrito del usuario"""
    try:
        cart_ref = st.session_state.db.collection('carts').document(user_id)
        cart_doc = cart_ref.get()
        
        if cart_doc.exists:
            return cart_doc.to_dict().get('items', [])
        return []
    
    except Exception as e:
        st.error(f"Error al obtener carrito: {str(e)}")
        return []

# Funciones de Stripe
def create_checkout_session(items, user_email):
    """Crea una sesión de pago con Stripe"""
    try:
        line_items = []
        for item in items:
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': item['name'],
                        'images': [item['image']],
                    },
                    'unit_amount': int(item['price'] * 100),
                },
                'quantity': item['quantity'],
            })
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='http://localhost:8501?payment=success&session_id={CHECKOUT_SESSION_ID}',
            cancel_url='http://localhost:8501?payment=cancelled',
            customer_email=user_email,
            metadata={
                'user_id': st.session_state['usuario']['uid'],
                'user_name': st.session_state['usuario']['nombre']
            }
        )
        
        return checkout_session.url, checkout_session.id
    
    except Exception as e:
        st.error(f"Error al crear sesión de pago: {str(e)}")
        return None

# FUNCIÓN CORREGIDA
def save_cart_to_firestore(session_id, user_id, cart_items):
    """Guarda el carrito en Firestore antes de ir a Stripe"""
    try:
        # Convertir items del carrito al formato correcto
        formatted_items = []
        for item in cart_items:
            formatted_items.append({
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'image': item.get('image', ''),
                'added_at': datetime.now()
            })
        
        cart_data = {
            'session_id': session_id,
            'user_id': user_id,
            'items': formatted_items,
            'created_at': datetime.now(),
            'status': 'pending_payment'
        }
        
        # CORREGIDO: Usar set() con document específico
        st.session_state.db.collection('carts').document(session_id).set(cart_data)
        st.success("Carrito guardado en Firebase")
        
    except Exception as e:
        st.error(f"Error al guardar carrito: {str(e)}")

# Funciones para manejar el carrito (agregar a catalogo.py)
def remove_from_cart(product_name):
    """Elimina un producto del carrito por nombre - ACTUALIZADO PARA FIREBASE"""
    try:
        # 1. Actualizar en session_state
        st.session_state.cart = [item for item in st.session_state.cart if item['name'] != product_name]
        
        # 2. Actualizar en Firebase
        if 'usuario' in st.session_state and st.session_state.usuario:
            user_id = st.session_state.usuario['uid']
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            
            # Convertir session_state.cart a formato Firebase
            firebase_items = []
            for item in st.session_state.cart:
                firebase_items.append({
                    'name': item['name'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'image': item.get('image', ''),
                    'product_id': item.get('product_id', item['name']),  # usar name como fallback
                    'added_at': datetime.now()
                })
            
            # Actualizar el documento completo
            cart_ref.update({
                'items': firebase_items,
                'updated_at': datetime.now()
            })
            
            st.success(f"✅ '{product_name}' eliminado del carrito (Firebase actualizado)")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al eliminar del carrito: {str(e)}")
        return False

def update_cart_quantity(product_name, new_quantity):
    """Actualiza la cantidad de un producto en el carrito - ACTUALIZADO PARA FIREBASE"""
    try:
        # 1. Actualizar en session_state
        for item in st.session_state.cart:
            if item['name'] == product_name:
                if new_quantity <= 0:
                    # Si la cantidad es 0 o menos, eliminar el producto
                    st.session_state.cart = [i for i in st.session_state.cart if i['name'] != product_name]
                else:
                    item['quantity'] = new_quantity
                break
        
        # 2. Actualizar en Firebase
        if 'usuario' in st.session_state and st.session_state.usuario:
            user_id = st.session_state.usuario['uid']
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            
            # Convertir session_state.cart a formato Firebase
            firebase_items = []
            for item in st.session_state.cart:
                firebase_items.append({
                    'name': item['name'],
                    'price': item['price'],
                    'quantity': item['quantity'],
                    'image': item.get('image', ''),
                    'product_id': item.get('product_id', item['name']),
                    'added_at': datetime.now()
                })
            
            # Actualizar el documento completo
            cart_ref.update({
                'items': firebase_items,
                'updated_at': datetime.now()
            })
            
            if new_quantity <= 0:
                st.success(f"✅ '{product_name}' eliminado (Firebase actualizado)")
            else:
                st.success(f"✅ Cantidad de '{product_name}' actualizada a {new_quantity} (Firebase actualizado)")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al actualizar cantidad: {str(e)}")
        return False

def clear_entire_cart():
    """Vacía todo el carrito - ACTUALIZADO PARA FIREBASE"""
    try:
        # 1. Limpiar session_state
        st.session_state.cart = []
        
        # 2. Limpiar en Firebase
        if 'usuario' in st.session_state and st.session_state.usuario:
            user_id = st.session_state.usuario['uid']
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            
            # Verificar si existe el documento antes de actualizarlo
            cart_doc = cart_ref.get()
            
            if cart_doc.exists:
                # Actualizar con carrito vacío
                cart_ref.update({
                    'items': [],
                    'updated_at': datetime.now(),
                    'cleared_at': datetime.now()
                })
                st.success("✅ Carrito vaciado completamente (Firebase actualizado)")
            else:
                st.info("ℹ️ No había carrito en Firebase para limpiar")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al vaciar carrito: {str(e)}")
        return False
    
def sync_cart_with_firebase():
    """Sincroniza el carrito de session_state con Firebase"""
    try:
        if not ('usuario' in st.session_state and st.session_state.usuario):
            return False
            
        user_id = st.session_state.usuario['uid']
        cart_ref = st.session_state.db.collection('carts').document(user_id)
        
        # Convertir session_state.cart a formato Firebase
        firebase_items = []
        for item in st.session_state.cart:
            firebase_items.append({
                'name': item['name'],
                'price': item['price'],
                'quantity': item['quantity'],
                'image': item.get('image', ''),
                'product_id': item.get('product_id', item['name']),
                'added_at': datetime.now()
            })
        
        # Actualizar o crear el documento
        cart_data = {
            'user_id': user_id,
            'items': firebase_items,
            'updated_at': datetime.now()
        }
        
        cart_ref.set(cart_data, merge=True)
        return True
        
    except Exception as e:
        st.error(f"❌ Error sincronizando carrito: {str(e)}")
        return False

def load_cart_from_firebase():
    """Carga el carrito desde Firebase al session_state"""
    try:
        if not ('usuario' in st.session_state and st.session_state.usuario):
            return []
            
        user_id = st.session_state.usuario['uid']
        cart_ref = st.session_state.db.collection('carts').document(user_id)
        cart_doc = cart_ref.get()
        
        if cart_doc.exists:
            cart_data = cart_doc.to_dict()
            firebase_items = cart_data.get('items', [])
            
            # Convertir de formato Firebase a formato session_state
            session_items = []
            for item in firebase_items:
                session_items.append({
                    'name': item.get('name', ''),
                    'price': item.get('price', 0),
                    'quantity': item.get('quantity', 1),
                    'image': item.get('image', ''),
                    'product_id': item.get('product_id', item.get('name', ''))
                })
            
            return session_items
        
        return []
        
    except Exception as e:
        st.error(f"❌ Error cargando carrito desde Firebase: {str(e)}")
        return []

def add_to_cart_improved(product, user_id):
    """Versión mejorada de agregar al carrito que mantiene sincronización"""
    try:
        # 1. Agregar/actualizar en session_state
        cart_item = {
            'name': product['name'],
            'price': product['price'],
            'quantity': 1,
            'image': product['image'],
            'product_id': product.get('id', product['name'])
        }
        
        # Verificar si ya existe en el carrito
        existing_item = next((item for item in st.session_state.cart 
                            if item['name'] == product['name']), None)
        
        if existing_item:
            existing_item['quantity'] += 1
        else:
            st.session_state.cart.append(cart_item)
        
        # 2. Sincronizar con Firebase
        sync_cart_with_firebase()
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error al agregar al carrito: {str(e)}")
        return False

# Funciones adicionales para debugging
def show_cart_debug_info():
    """Muestra información de debug del carrito"""
    st.write("### 🔍 Debug Info del Carrito")
    st.write(f"**Session Cart Length:** {len(st.session_state.cart)}")
    st.write(f"**Session Cart:** {st.session_state.cart}")
    
    if 'usuario' in st.session_state and st.session_state.usuario:
        user_id = st.session_state.usuario['uid']
        try:
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            cart_doc = cart_ref.get()
            if cart_doc.exists:
                firebase_cart = cart_doc.to_dict()
                st.write(f"**Firebase Cart:** {firebase_cart}")
            else:
                st.write("**Firebase Cart:** No existe")
        except Exception as e:
            st.write(f"**Firebase Error:** {str(e)}")

def emergency_cart_cleanup():
    """Limpieza de emergencia del carrito"""
    try:
        # Limpiar session_state
        st.session_state.cart = []
        
        # Forzar limpieza en Firebase
        if 'usuario' in st.session_state and st.session_state.usuario:
            user_id = st.session_state.usuario['uid']
            cart_ref = st.session_state.db.collection('carts').document(user_id)
            cart_ref.delete()
        
        # Limpiar otros posibles estados relacionados
        for key in list(st.session_state.keys()):
            if 'cart' in key.lower():
                if key != 'cart':  # Mantener el cart principal
                    del st.session_state[key]
        
        st.success("🚨 Limpieza de emergencia completada")
        return True
        
    except Exception as e:
        st.error(f"❌ Error en limpieza de emergencia: {str(e)}")
        return False

def verify_cart_empty():
    """Verifica que el carrito esté vacío"""
    try:
        if len(st.session_state.cart) == 0:
            st.success("✅ Carrito verificado como vacío")
            return True
        else:
            st.warning(f"⚠️ Carrito no está vacío: {len(st.session_state.cart)} items")
            return False
    except Exception as e:
        st.error(f"❌ Error verificando carrito: {str(e)}")
        return False

def force_cart_refresh():
    """Fuerza la actualización visual del carrito"""
    try:
        # Incrementar trigger de refresh
        if 'cart_refresh_trigger' not in st.session_state:
            st.session_state.cart_refresh_trigger = 0
        st.session_state.cart_refresh_trigger += 1
        
        return True
    except Exception as e:
        st.error(f"❌ Error forzando refresh: {str(e)}")
        return False

def update_product_stock(items):
    """Actualiza el stock de productos después de la compra"""
    try:
        for item in items:
            # Buscar producto por nombre
            products_ref = st.session_state.db.collection('products')
            query = products_ref.where('name', '==', item['name'])
            docs = list(query.stream())
            
            for doc in docs:
                product_data = doc.to_dict()
                current_stock = product_data.get('stock', 0)
                new_stock = max(0, current_stock - item['quantity'])
                
                doc.reference.update({
                    'stock': new_stock,
                    'last_updated': datetime.now()
                })
                
                st.info(f"📦 Stock actualizado: {item['name']} ({current_stock} → {new_stock})")
                
    except Exception as e:
        st.error(f"❌ Error actualizando stock: {str(e)}")

# --- LÓGICA PRINCIPAL DE LA PÁGINA ---

# Header principal 
st.markdown('''
<div class="main-header">
    <h1>ADRIANA TOUZ</h1>
    <p>Bienvenido a tu tienda de moda exclusiva</p>
</div>
''', unsafe_allow_html=True)

# Sidebar con logo, información del usuario y carrito
with st.sidebar:
    # Logo en la sidebar
    st.image("logo.jpg", width=150)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # CARGAR CARRITO DESDE FIREBASE AL INICIAR
    if 'cart_loaded' not in st.session_state:
        firebase_cart = load_cart_from_firebase()
        if firebase_cart:
            st.session_state.cart = firebase_cart
            st.success(f"✅ Carrito cargado: {len(firebase_cart)} productos")
        st.session_state.cart_loaded = True
    
    # BOTONES DE DEPURACIÓN
    if st.button("🧪 Probar Firebase"):
        if test_firebase_connection():
            st.success("✅ Firebase conectado correctamente")
        else:
            st.error("❌ Error de conexión a Firebase")
    
    if st.button("🔄 Sincronizar Carrito"):
        if sync_cart_with_firebase():
            st.success("✅ Carrito sincronizado con Firebase")
        else:
            st.error("❌ Error al sincronizar carrito")

    # Información del usuario
    st.markdown(f"### 👤 {st.session_state['usuario']['nombre']}")
    
    if st.button("🚪 Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()
    
    st.markdown("---")
    
    # CARRITO MEJORADO
    def render_improved_sidebar_cart():
        """Renderiza el carrito en sidebar con manejo mejorado"""
        
        # Botón de debug (solo mostrar en desarrollo)
        if st.button("🔍 Debug Carrito", key="debug_cart"):
            show_cart_debug_info()
        
        # Botón de limpieza de emergencia
        if st.button("🚨 Limpiar Carrito (Emergencia)", key="emergency_clean"):
            if emergency_cart_cleanup():
                st.rerun()
        
        st.markdown("### 🛒 Carrito")
        
        # Verificar si hay trigger para actualizar
        refresh_trigger = st.session_state.get('cart_refresh_trigger', 0)
        
        if st.session_state.cart:
            total = 0
            
            st.markdown('<div class="clear-cart-btn">', unsafe_allow_html=True)
            if st.button("🗑️ Vaciar Todo", key=f"clear_all_{refresh_trigger}"):
                if clear_entire_cart():
                    st.success("✅ Carrito vaciado")
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Mostrar items del carrito
            for idx, item in enumerate(st.session_state.cart):
                st.markdown(f"""
                <div class="cart-item">
                    <strong>{item['name']}</strong><br>
                    <small>${item['price']:.2f} c/u</small><br>
                    <span style="color: #5D4037;">Subtotal: ${item['price'] * item['quantity']:.2f}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("➖", key=f"decrease_{idx}_{refresh_trigger}"):
                        new_quantity = item['quantity'] - 1
                        if update_cart_quantity(item['name'], new_quantity):
                            st.rerun()
                
                with col2:
                    st.markdown(f"""
                    <div class="quantity-display">
                        {item['quantity']}
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if st.button("➕", key=f"increase_{idx}_{refresh_trigger}"):
                        new_quantity = item['quantity'] + 1
                        if update_cart_quantity(item['name'], new_quantity):
                            st.rerun()
                
                st.markdown('<div class="remove-item-btn">', unsafe_allow_html=True)
                if st.button(f"🗑️ Quitar", key=f"remove_{idx}_{refresh_trigger}"):
                    if remove_from_cart(item['name']):
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                total += item['price'] * item['quantity']
            
            # Mostrar total
            st.markdown(f"""
            <div class="cart-total">
                💰 Total: ${total:.2f}
            </div>
            """, unsafe_allow_html=True)

            # Botones de compra
            st.markdown("### 💳 Métodos de Pago")
            
            # Botón mejorado de compra simulada
            st.markdown('<div class="simulated-checkout-btn">', unsafe_allow_html=True)
            if st.button("🛒 Comprar Ahora (Simulado)", key=f"simulated_checkout_{refresh_trigger}", use_container_width=True):
                if process_simulated_checkout_improved():
                    st.rerun()  # Recargar para mostrar carrito vacío
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Separador
            st.markdown('<div class="payment-separator">O con Stripe</div>', unsafe_allow_html=True)
            
            # Botón original con Stripe
            if st.button("💳 Pagar con Stripe", key=f"stripe_checkout_{refresh_trigger}", use_container_width=True):
                checkout_url, session_id = create_checkout_session(st.session_state.cart, st.session_state['usuario']['email'])
                if checkout_url and session_id:
                    save_cart_to_firestore(session_id, st.session_state['usuario']['uid'], st.session_state.cart)
                    st.link_button("🔗 Ir a Stripe Checkout", checkout_url, use_container_width=True)
                    st.success("¡Sesión de pago creada! Haz clic en el botón para continuar.")
        else:
            # Carrito vacío
            st.markdown("""
            <div class="empty-cart">
                <img src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=200&h=200&fit=crop" 
                     alt="Carrito vacío">
                <p><strong>Tu carrito está vacío</strong></p>
                <p style="font-size: 0.9rem;">¡Comienza a agregar productos!</p>
            </div>
            """, unsafe_allow_html=True)

    # Llamar a la función para renderizar el carrito
    render_improved_sidebar_cart()

# Contenido principal - Catálogo de productos
st.markdown("## Catálogo de Productos")

# Obtener productos
products = get_products()

if products:
    display_personalized_offers(st.session_state['usuario']['uid'], products)

# Filtros - ARREGLADO CON KEY ÚNICO
col1, col2 = st.columns([1, 3])
with col1:
    categories = ["todos", "vestidos", "blusas", "pantalones", "chaquetas", "zapatos", "accesorios"]
    selected_category = st.selectbox("Categoría", categories, key="category_filter_main")

# Filtrar por categoría
if selected_category != "todos":
    products = [p for p in products if p.get('category') == selected_category]

# Mostrar productos en grid - VERSIÓN CORREGIDA
if products:
    # Crear grid responsivo
    cols = st.columns(3)
    
    for idx, product in enumerate(products):
        with cols[idx % 3]:
            # Crear contenedor con altura uniforme
            st.markdown(f"""
            <div class="product-card">
                <div class="product-image-container">
                    <img src="{product['image']}" alt="{product['name']}">
                </div>
                <div class="product-content">
                    <div>
                        <h3 class="product-title">{product['name']}</h3>
                        <p class="product-description">{product['description']}</p>
                    </div>
                    <div class="product-pricing">
                        <div class="price-tag">${product['price']:.2f}</div>
                        <p class="stock-info">Stock: {product.get('stock', 0)} unidades</p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Botón fuera del HTML para mantener funcionalidad
            if st.button(f"🛒 Agregar al Carrito", 
                        key=f"add_product_{product.get('id', idx)}_{idx}",
                        use_container_width=True):
                try:
                    if product.get('stock', 0) <= 0:
                        st.error("❌ Producto sin stock disponible")
                    else:
                        if add_to_cart_improved(product, st.session_state.usuario['uid']):
                            existing_item = next((item for item in st.session_state.cart 
                                                if item['name'] == product['name']), None)
                            
                            if existing_item and existing_item['quantity'] > 1:
                                st.success(f"✅ Cantidad actualizada: {product['name']} (x{existing_item['quantity']})")
                            else:
                                st.success(f"✅ {product['name']} agregado al carrito!")
                            
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar producto")
                            
                except Exception as e:
                    st.error(f"❌ Error al agregar producto: {str(e)}")
            
            # Espaciado adicional entre productos
            st.markdown("<br>", unsafe_allow_html=True)

else:
    st.info("No se encontraron productos en esta categoría.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem;">
    <p>ADRIANA TOUZ - Tu estilo, nuestra pasión</p>
    <p>Desarrollado usando Streamlit, Firebase y Stripe</p>
</div>
""", unsafe_allow_html=True)