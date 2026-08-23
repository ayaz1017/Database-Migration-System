export const initialNodes = [
  {
    id: 'users',
    type: 'tableNode',
    position: { x: 50, y: 100 },
    data: {
      tableName: 'users',
      dialect: 'PostgreSQL',
      columns: [
        { name: 'id', type: 'UUID', isPrimary: true, isForeign: false },
        { name: 'email', type: 'VARCHAR(255)', isPrimary: false, isForeign: false },
        { name: 'full_name', type: 'VARCHAR(100)', isPrimary: false, isForeign: false },
        { name: 'role', type: 'VARCHAR(50)', isPrimary: false, isForeign: false },
        { name: 'created_at', type: 'TIMESTAMP', isPrimary: false, isForeign: false },
        { name: 'is_active', type: 'BOOLEAN', isPrimary: false, isForeign: false }
      ],
      ddlOriginal: `CREATE TABLE users (\n  id UNIQUEIDENTIFIER PRIMARY KEY,\n  email NVARCHAR(255) NOT NULL,\n  full_name NVARCHAR(100),\n  role NVARCHAR(50),\n  created_at DATETIME2 DEFAULT SYSDATETIME(),\n  is_active BIT DEFAULT 1\n);`,
      ddlTarget: `CREATE TABLE users (\n  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n  email VARCHAR(255) NOT NULL,\n  full_name VARCHAR(100),\n  role VARCHAR(50),\n  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n  is_active BOOLEAN DEFAULT TRUE\n);`
    }
  },
  {
    id: 'categories',
    type: 'tableNode',
    position: { x: 50, y: 460 },
    data: {
      tableName: 'categories',
      dialect: 'Oracle',
      columns: [
        { name: 'id', type: 'NUMBER', isPrimary: true, isForeign: false },
        { name: 'name', type: 'VARCHAR2(100)', isPrimary: false, isForeign: false },
        { name: 'slug', type: 'VARCHAR2(100)', isPrimary: false, isForeign: false },
        { name: 'parent_id', type: 'NUMBER', isPrimary: false, isForeign: true }
      ],
      ddlOriginal: `CREATE TABLE categories (\n  id NUMBER PRIMARY KEY,\n  name VARCHAR2(100) NOT NULL,\n  slug VARCHAR2(100) UNIQUE,\n  parent_id NUMBER REFERENCES categories(id)\n);`,
      ddlTarget: `CREATE TABLE categories (\n  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,\n  name VARCHAR(100) NOT NULL,\n  slug VARCHAR(100) UNIQUE,\n  parent_id BIGINT REFERENCES categories(id)\n);`
    }
  },
  {
    id: 'products',
    type: 'tableNode',
    position: { x: 420, y: 460 },
    data: {
      tableName: 'products',
      dialect: 'PostgreSQL',
      columns: [
        { name: 'id', type: 'UUID', isPrimary: true, isForeign: false },
        { name: 'category_id', type: 'NUMBER', isPrimary: false, isForeign: true },
        { name: 'title', type: 'VARCHAR(255)', isPrimary: false, isForeign: false },
        { name: 'price', type: 'NUMERIC(10,2)', isPrimary: false, isForeign: false },
        { name: 'stock_qty', type: 'INTEGER', isPrimary: false, isForeign: false },
        { name: 'sku', type: 'VARCHAR(50)', isPrimary: false, isForeign: false }
      ],
      ddlOriginal: `CREATE TABLE products (\n  id UNIQUEIDENTIFIER PRIMARY KEY,\n  category_id INT FOREIGN KEY REFERENCES categories(id),\n  title NVARCHAR(255) NOT NULL,\n  price DECIMAL(10,2) NOT NULL,\n  stock_qty INT DEFAULT 0,\n  sku NVARCHAR(50)\n);`,
      ddlTarget: `CREATE TABLE products (\n  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n  category_id BIGINT REFERENCES categories(id),\n  title VARCHAR(255) NOT NULL,\n  price NUMERIC(10,2) NOT NULL,\n  stock_qty INTEGER DEFAULT 0,\n  sku VARCHAR(50)\n);`
    }
  },
  {
    id: 'orders',
    type: 'tableNode',
    position: { x: 420, y: 100 },
    data: {
      tableName: 'orders',
      dialect: 'MSSQL',
      columns: [
        { name: 'id', type: 'UNIQUEIDENTIFIER', isPrimary: true, isForeign: false },
        { name: 'user_id', type: 'UUID', isPrimary: false, isForeign: true },
        { name: 'total_amount', type: 'DECIMAL(12,2)', isPrimary: false, isForeign: false },
        { name: 'status', type: 'NVARCHAR(50)', isPrimary: false, isForeign: false },
        { name: 'order_date', type: 'DATETIME2', isPrimary: false, isForeign: false }
      ],
      ddlOriginal: `CREATE TABLE orders (\n  id UNIQUEIDENTIFIER PRIMARY KEY,\n  user_id UNIQUEIDENTIFIER FOREIGN KEY REFERENCES users(id),\n  total_amount DECIMAL(12,2),\n  status NVARCHAR(50),\n  order_date DATETIME2\n);`,
      ddlTarget: `CREATE TABLE orders (\n  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n  user_id UUID REFERENCES users(id),\n  total_amount NUMERIC(12,2),\n  status VARCHAR(50),\n  order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n);`
    }
  },
  {
    id: 'order_items',
    type: 'tableNode',
    position: { x: 790, y: 260 },
    data: {
      tableName: 'order_items',
      dialect: 'MySQL',
      columns: [
        { name: 'id', type: 'BIGINT', isPrimary: true, isForeign: false },
        { name: 'order_id', type: 'UNIQUEIDENTIFIER', isPrimary: false, isForeign: true },
        { name: 'product_id', type: 'UUID', isPrimary: false, isForeign: true },
        { name: 'quantity', type: 'INT', isPrimary: false, isForeign: false },
        { name: 'unit_price', type: 'DECIMAL(10,2)', isPrimary: false, isForeign: false }
      ],
      ddlOriginal: `CREATE TABLE order_items (\n  id BIGINT AUTO_INCREMENT PRIMARY KEY,\n  order_id CHAR(36) NOT NULL,\n  product_id CHAR(36) NOT NULL,\n  quantity INT NOT NULL,\n  unit_price DECIMAL(10,2)\n);`,
      ddlTarget: `CREATE TABLE order_items (\n  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,\n  order_id UUID REFERENCES orders(id) ON DELETE CASCADE,\n  product_id UUID REFERENCES products(id),\n  quantity INTEGER NOT NULL,\n  unit_price NUMERIC(10,2)\n);`
    }
  }
];

export const initialEdges = [
  {
    id: 'e-users-orders',
    source: 'users',
    target: 'orders',
    animated: true,
    style: { stroke: '#7c3aed', strokeWidth: 2 }
  },
  {
    id: 'e-categories-products',
    source: 'categories',
    target: 'products',
    animated: true,
    style: { stroke: '#7c3aed', strokeWidth: 2 }
  },
  {
    id: 'e-orders-items',
    source: 'orders',
    target: 'order_items',
    animated: true,
    style: { stroke: '#7c3aed', strokeWidth: 2 }
  },
  {
    id: 'e-products-items',
    source: 'products',
    target: 'order_items',
    animated: true,
    style: { stroke: '#7c3aed', strokeWidth: 2 }
  }
];
