import streamlit as st
import stripe
import os
from datetime import datetime
import time

# Verificar si el usuario está logueado
if 'login' not in st.session_state:
    st.switch_page('app.py')

# Configuración de Stripe
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# CSS personalizado para el diseño de lujo
with open("estilos/css_compra.html", "r") as file:
    html_content = file.read()
st.markdown(html_content, unsafe_allow_html=True)

# FUNCIÓN COMPLETAMENTE CORREGIDA
def save_order_to_firestore(session_id, user_id, items, total):
    """Guarda la orden en Firestore - VERSIÓN CORREGIDA"""
    try:
        # Formatear items correctamente
        formatted_items = []
        for item in items:
            formatted_items.append({
                'name': item['name'],
                'price': float(item['price']),  # Asegurar que sea float
                'quantity': int(item['quantity']),  # Asegurar que sea int
                'image': item.get('image', ''),
                'subtotal': float(item['price']) * int(item['quantity'])
            })
        
        order_number = f"ORD-{int(time.time())}-{user_id[:8]}"
        
        order_data = {
            'order_number': order_number,
            'user_id': user_id,
            'user_name': st.session_state['usuario']['nombre'],
            'user_email': st.session_state['usuario']['email'],
            'items': formatted_items,
            'total': float(total),
            'session_id': session_id,
            'status': 'completed',
            'created_at': datetime.now(),
            'payment_method': 'stripe',
            'currency': 'USD'
        }
        
        # CORREGIDO: Usar add() que retorna DocumentReference
        doc_ref = st.session_state.db.collection('orders').add(order_data)
        
        # Verificar que se creó correctamente
        if doc_ref and len(doc_ref) > 1:  # add() retorna (timestamp, doc_ref)
            document_ref = doc_ref[1]
            st.success(f"✅ Orden guardada con ID: {document_ref.id}")
            return order_number
        else:
            st.error("❌ Error: No se pudo crear la orden")
            return None
        
    except Exception as e:
        st.error(f"❌ Error al guardar la orden: {str(e)}")
        return None

# FUNCIÓN MEJORADA
def clear_user_cart(session_id):
    """Limpia el carrito del usuario después de la compra - MEJORADO"""
    try:
        # Verificar si el documento existe antes de eliminarlo
        cart_ref = st.session_state.db.collection('carts').document(session_id)
        cart_doc = cart_ref.get()
        
        if cart_doc.exists:
            cart_ref.delete()
            st.success("✅ Carrito limpiado en Firebase")
        else:
            st.warning("⚠️ No se encontró carrito en Firebase para limpiar")
        
        # Limpiar carrito en session_state
        if 'cart' in st.session_state:
            st.session_state.cart = []
            st.success("✅ Carrito limpiado en sesión")
        
    except Exception as e:
        st.error(f"❌ Error al limpiar carrito: {str(e)}")

def get_stripe_session_details(session_id):
    """Obtiene los detalles de la sesión de Stripe"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return session
    except Exception as e:
        st.error(f"Error al obtener detalles de Stripe: {str(e)}")
        return None

# FUNCIÓN MEJORADA
def update_product_stock(items):
    """Actualiza el stock de los productos comprados - MEJORADO"""
    try:
        updates_count = 0
        
        for item in items:
            try:
                # Buscar el producto por nombre
                products_ref = st.session_state.db.collection('products')
                query = products_ref.where('name', '==', item['name'])
                docs = list(query.stream())  # Convertir a lista
                
                if not docs:
                    st.warning(f"⚠️ Producto '{item['name']}' no encontrado para actualizar stock")
                    continue
                
                for doc in docs:
                    product_data = doc.to_dict()
                    current_stock = product_data.get('stock', 0)
                    new_stock = max(0, current_stock - item['quantity'])
                    
                    # Actualizar stock
                    doc.reference.update({
                        'stock': new_stock,
                        'last_updated': datetime.now()
                    })
                    
                    updates_count += 1
                    st.info(f"📦 Stock actualizado para '{item['name']}': {current_stock} → {new_stock}")
                    
            except Exception as item_error:
                st.error(f"❌ Error actualizando '{item['name']}': {str(item_error)}")
                continue
        
        if updates_count > 0:
            st.success(f"✅ {updates_count} productos actualizados")
        else:
            st.warning("⚠️ No se actualizó ningún producto")
                
    except Exception as e:
        st.error(f"❌ Error general al actualizar stock: {str(e)}")

# FUNCIÓN MEJORADA
def restore_cart_from_firestore(session_id):
    """Restaura el carrito desde Firestore - MEJORADO"""
    try:
        if not session_id:
            st.error("❌ Session ID no válido")
            return []

        # Intentar desde la colección 'carts'
        cart_ref = st.session_state.db.collection('carts').document(session_id)
        cart_doc = cart_ref.get()

        if cart_doc.exists:
            cart_data = cart_doc.to_dict()
            items = cart_data.get('items', [])

            if items:
                st.success(f"✅ Carrito restaurado: {len(items)} productos")
                return items
            else:
                st.warning("⚠️ Carrito encontrado pero vacío")
                return []
        else:
            st.error(f"❌ No se encontró carrito con session_id: {session_id}")
            return []

    except Exception as e:
        st.error(f"❌ Error al restaurar carrito: {str(e)}")
        return []
    
# Verificar estado de la orden
def verify_order_creation(order_number):
    """Verifica que la orden se haya creado correctamente"""
    try:
        orders_ref = st.session_state.db.collection('orders')
        query = orders_ref.where('order_number', '==', order_number)
        docs = list(query.stream())
        
        if docs:
            st.success(f"✅ Orden verificada en Firebase: {order_number}")
            return True
        else:
            st.error(f"❌ Orden no encontrada en Firebase: {order_number}")
            return False
            
    except Exception as e:
        st.error(f"❌ Error verificando orden: {str(e)}")
        return False

# --- LÓGICA PRINCIPAL ---
st.markdown('''
<div class="success-container">
    <div class="success-icon">🎉</div>
    <h1>¡Compra Realizada!</h1>
    <p>Gracias por tu compra. Tu pedido ya ha sido procesado.</p>
</div>
''', unsafe_allow_html=True)

# Obtener session_id de session_state (viene desde app.py) o query_params
session_id = None

# Primer intento: desde session_state (redirección desde app.py)
if 'stripe_session_id' in st.session_state and st.session_state.get('payment_success', False):
    session_id = st.session_state['stripe_session_id']

    # Limpiar session_state después de usar
    del st.session_state['stripe_session_id']
    del st.session_state['payment_success']

# Segundo intento: desde query_params (acceso directo)
else:
    query_params = st.query_params
    session_id = query_params.get('session_id')

# Verificar si tenemos session_id para proceder
if not session_id:
    st.error("❌ No se encontró información del pago.")
    if st.button("🔙 Volver al Catálogo"):
        st.switch_page('pages/catalogo.py')
    st.stop()

# Obtener detalles de la sesión de Stripe
session = get_stripe_session_details(session_id)

if not session:
    st.error("❌ No se pudieron obtener los detalles del pago.")
    if st.button("🔙 Volver al Catálogo"):
        st.switch_page('pages/catalogo.py')
    st.stop()

# Mostrar detalles del pedido
st.markdown(f'''
<div class="order-details">
    <h2>📋 Detalles del Pedido</h2>
    <div class="order-summary">
        <strong>Cliente:</strong> {st.session_state['usuario']['nombre']}<br>
        <strong>Email:</strong> {st.session_state['usuario']['email']}<br>
        <strong>Estado del Pago:</strong> ✅ Completado<br>
        <strong>ID de Sesión:</strong> {session_id}
    </div>
</div>
''', unsafe_allow_html=True)

# Restaurar carrito si no está en session_state o está vacío
if not st.session_state.get('cart') or len(st.session_state.cart) == 0:
    st.session_state.cart = restore_cart_from_firestore(session_id)

# Verificar si tenemos productos para mostrar
if not st.session_state.cart or len(st.session_state.cart) == 0:
    st.error("❌ No se pudieron recuperar los productos del carrito.")
    st.info("💡 Esto puede ocurrir si el carrito se vació antes de completar el pago.")
    if st.button("🔙 Volver al Catálogo"):
        st.switch_page('catalogo.py')
    st.stop()

# Mostrar productos comprados
st.markdown('<h3>Productos Comprados</h3>', unsafe_allow_html=True)

# Construir HTML de productos
products_html = ""
total = 0
for item in st.session_state.cart:
    products_html += f'''
    <div class="order-item">
        <div>
            <strong>{item['name']}</strong><br>
            <small>Cantidad: {item['quantity']}</small>
        </div>
        <div>${item['price']:.2f}</div>
    </div>
    '''
    total += item['price'] * item['quantity']

# Mostrar productos y total
st.markdown(products_html, unsafe_allow_html=True)
st.markdown(f'<div class="total-amount">Total: ${total:.2f}</div>', unsafe_allow_html=True)

# Guardar orden en Firestore
order_number = save_order_to_firestore(
    session_id, 
    st.session_state['usuario']['uid'], 
    st.session_state.cart, 
    total
)

if order_number:
    st.success(f"📝 Número de orden: {order_number}")
    
    # Verificar que la orden se creó correctamente
    verify_order_creation(order_number)
    
    # Actualizar stock de productos
    update_product_stock(st.session_state.cart)
    
    # Limpiar carrito después de guardar la orden
    clear_user_cart(session_id)
    
    # Mostrar mensaje de confirmación
    st.info("📧 Se ha enviado un email de confirmación a tu dirección de correo.")
    
else:
    st.error("❌ Hubo un problema al guardar la orden. Por favor, contacta al soporte.")

# Botón para continuar comprando
st.markdown('''
<div style="text-align: center; margin: 2rem 0;">
</div>
''', unsafe_allow_html=True)
if st.button("Continuar Comprando", key="continue_shopping"):
    # Limpiar parámetros de la URL
    st.query_params.clear()
    st.switch_page('pages/catalogo.py')

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 1rem;">
    <p>ADRIANA TOUZ - Gracias por confiar en nosotros</p>
</div>
""", unsafe_allow_html=True)
