# test_orders.py - Script independiente para crear órdenes de prueba

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time

def create_test_orders():
    """Crea órdenes de prueba en Firebase"""
    try:
        # Inicializar Firebase (solo si no está inicializado)
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Datos de prueba
        test_orders = [
            {
                'order_number': f"TEST-001-{int(time.time())}",
                'user_id': 'test_user_1',
                'user_name': 'Usuario Prueba 1',
                'user_email': 'test1@example.com',
                'items': [
                    {
                        'name': 'Vestido Elegante',
                        'price': 89.99,
                        'quantity': 1,
                        'image': 'https://i.imgur.com/TRmtJwn.jpg',
                        'subtotal': 89.99
                    },
                    {
                        'name': 'Bolso de Mano',
                        'price': 65.99,
                        'quantity': 2,
                        'image': 'https://i.imgur.com/T99kfQS.jpg',
                        'subtotal': 131.98
                    }
                ],
                'total': 221.97,
                'session_id': f'test_session_{int(time.time())}_1',
                'status': 'completed',
                'payment_status': 'test_paid',
                'payment_method': 'test_simulation',
                'currency': 'USD',
                'created_at': datetime.now(),
                'test_mode': True
            },
            {
                'order_number': f"TEST-002-{int(time.time())}",
                'user_id': 'test_user_2',
                'user_name': 'Usuario Prueba 2',
                'user_email': 'test2@example.com',
                'items': [
                    {
                        'name': 'Blazer',
                        'price': 129.99,
                        'quantity': 1,
                        'image': 'https://i.imgur.com/yCMtdfa.jpg',
                        'subtotal': 129.99
                    }
                ],
                'total': 129.99,
                'session_id': f'test_session_{int(time.time())}_2',
                'status': 'completed',
                'payment_status': 'test_paid',
                'payment_method': 'test_simulation',
                'currency': 'USD',
                'created_at': datetime.now(),
                'test_mode': True
            }
        ]
        
        # Crear órdenes en Firebase
        created_orders = []
        for order in test_orders:
            doc_ref = db.collection('orders').add(order)
            if doc_ref and len(doc_ref) > 1:
                created_orders.append({
                    'order_number': order['order_number'],
                    'doc_id': doc_ref[1].id
                })
                print(f"✅ Orden creada: {order['order_number']} (ID: {doc_ref[1].id})")
        
        print(f"\n🎉 {len(created_orders)} órdenes de prueba creadas exitosamente!")
        
        # Verificar que se crearon
        orders_ref = db.collection('orders')
        all_orders = list(orders_ref.stream())
        print(f"📊 Total de órdenes en la base de datos: {len(all_orders)}")
        
        return created_orders
        
    except Exception as e:
        print(f"❌ Error creando órdenes de prueba: {str(e)}")
        return []

def verify_orders():
    """Verifica las órdenes en la base de datos"""
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate('serviceAccountKey.json')
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        orders_ref = db.collection('orders')
        orders = list(orders_ref.stream())
        
        print(f"📋 Órdenes encontradas: {len(orders)}")
        
        for i, order_doc in enumerate(orders[-5:], 1):  # Mostrar últimas 5
            order_data = order_doc.to_dict()
            print(f"\n--- Orden {i} ---")
            print(f"Número: {order_data.get('order_number', 'N/A')}")
            print(f"Usuario: {order_data.get('user_name', 'N/A')}")
            print(f"Total: ${order_data.get('total', 0):.2f}")
            print(f"Estado: {order_data.get('status', 'N/A')}")
            print(f"Creada: {order_data.get('created_at', 'N/A')}")
            
    except Exception as e:
        print(f"❌ Error verificando órdenes: {str(e)}")

if __name__ == "__main__":
    print("🚀 Creando órdenes de prueba...")
    create_test_orders()
    
    print("\n🔍 Verificando órdenes...")
    verify_orders()