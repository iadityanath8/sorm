<?php

namespace ORM;

use PDO;
use PDOException;
use ReflectionClass;
use ReflectionProperty;

// Type mapping
class TypeMap {
    public static $map = [
        'int' => 'INTEGER',
        'string' => 'TEXT',
        'float' => 'REAL',
        'bool' => 'INTEGER'
    ];
}

// Attribute classes
class PrimaryKey {
    public $baseType;
    
    public function __construct($type = 'int') {
        $this->baseType = $type;
    }
    
    public function __toString() {
        $sqlType = TypeMap::$map[$this->baseType] ?? 'TEXT';
        return "$sqlType PRIMARY KEY AUTOINCREMENT";
    }
}

class ForeignKey {
    public $targetModel;
    
    public function __construct($targetModel) {
        $this->targetModel = $targetModel;
    }
    
    public function __toString() {
        $tableName = call_user_func([$this->targetModel, 'tableName']);
        return "INTEGER REFERENCES {$tableName}(id)";
    }
}

class NotNull {
    public $baseType;
    
    public function __construct($type) {
        $this->baseType = $type;
    }
    
    public function __toString() {
        $sqlType = TypeMap::$map[$this->baseType] ?? 'TEXT';
        return "$sqlType NOT NULL";
    }
}

class Unique {
    public $baseType;
    
    public function __construct($type) {
        $this->baseType = $type;
    }
    
    public function __toString() {
        $sqlType = TypeMap::$map[$this->baseType] ?? 'TEXT';
        return "$sqlType UNIQUE";
    }
}

class DefaultValue {
    public $value;
    
    public function __construct($value) {
        $this->value = $value;
    }
    
    public function __toString() {
        if (is_string($this->value)) {
            return "DEFAULT '{$this->value}'";
        }
        return "DEFAULT {$this->value}";
    }
}

class Check {
    public $expr;
    
    public function __construct($expr) {
        $this->expr = $expr;
    }
    
    public function __toString() {
        return "CHECK({$this->expr})";
    }
}

// Condition class
class Condition {
    private $expr;
    
    public function __construct($expr) {
        $this->expr = $expr;
    }
    
    public function andCondition(Condition $other) {
        return new Condition("({$this->expr}) AND ({$other->expr})");
    }
    
    public function orCondition(Condition $other) {
        return new Condition("({$this->expr}) OR ({$other->expr})");
    }
    
    public function not() {
        return new Condition("NOT ({$this->expr})");
    }
    
    public function __toString() {
        return $this->expr;
    }
}

// Field class
class Field {
    private $name;
    private $model;
    
    public function __construct($name, $model = null) {
        $this->name = $name;
        $this->model = $model;
    }
    
    public function eq($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} = {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} = {$quoted}");
    }
    
    public function ne($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} != {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} != {$quoted}");
    }
    
    public function gt($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} > {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} > {$quoted}");
    }
    
    public function lt($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} < {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} < {$quoted}");
    }
    
    public function gte($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} >= {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} >= {$quoted}");
    }
    
    public function lte($value) {
        if ($value instanceof Field) {
            return new Condition("{$this->fullName()} <= {$value->fullName()}");
        }
        $quoted = is_string($value) ? "'{$value}'" : $value;
        return new Condition("{$this->fullName()} <= {$quoted}");
    }
    
    public function in($values) {
        $vals = array_map(function($v) {
            return is_string($v) ? "'{$v}'" : $v;
        }, $values);
        $valStr = implode(", ", $vals);
        return new Condition("{$this->fullName()} IN ({$valStr})");
    }
    
    public function like($pattern) {
        return new Condition("{$this->fullName()} LIKE '{$pattern}'");
    }
    
    public function fullName() {
        if ($this->model) {
            $tableName = call_user_func([$this->model, 'tableName']);
            return "{$tableName}.{$this->name}";
        }
        return $this->name;
    }
    
    public function getModel() {
        return $this->model;
    }
}

// Base Model class
abstract class BaseModel {
    protected static $dbPath = 'app.db';
    protected static $connection = null;
    public static $foreignKeys = [];
    private static $fieldCache = [];
    
    public function __construct(array $data = []) {
        $fields = static::fields();
        foreach ($fields as $name => $type) {
            $this->$name = $data[$name] ?? null;
        }
    }
    
    // Magic method to get Field objects as static properties
    public static function __callStatic($name, $arguments) {
        // Check if it's a valid field name
        if (array_key_exists($name, static::fields())) {
            // Cache the Field object for performance
            $cacheKey = static::class . '::' . $name;
            if (!isset(self::$fieldCache[$cacheKey])) {
                self::$fieldCache[$cacheKey] = new Field($name, static::class);
            }
            return self::$fieldCache[$cacheKey];
        }
        throw new \BadMethodCallException("Unknown field or method: {$name}");
    }
    
    public static function connection() {
        if (static::$connection === null) {
            try {
                static::$connection = new PDO('sqlite:' . static::$dbPath);
                static::$connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            } catch (PDOException $e) {
                die("Connection failed: " . $e->getMessage());
            }
        }
        return static::$connection;
    }

    public function __toString() {
        $className = (new ReflectionClass($this))->getShortName();
        $fields = [];
        foreach (static::fields() as $name => $type) {
            $value = $this->$name ?? 'null';
            if (is_string($value)) {
                $value = "'{$value}'";
            }
            $fields[] = "{$name}={$value}";
        }
        return "{$className}(" . implode(", ", $fields) . ")";
    }
    
    public function __debugInfo() {
        $info = ['__class__' => get_class($this)];
        foreach (static::fields() as $name => $type) {
            $info[$name] = $this->$name ?? null;
        }
        return $info;
    }
    
    public static function tableName() {
        return strtolower((new ReflectionClass(static::class))->getShortName());
    }
    
    public static function primaryKey() {
        return 'id';
    }
    
    public static function fields() {
        // Override this in child classes
        return [];
    }
    
    public static function all() {
        $conn = static::connection();
        $tableName = static::tableName();
        $stmt = $conn->query("SELECT * FROM {$tableName}");
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        $objects = [];
        foreach ($rows as $row) {
            $objects[] = new static($row);
        }
        return $objects;
    }
    
    public static function filter($conditions = null, array $kwargs = []) {
        $tableName = static::tableName();
        $joins = [];
        $whereClause = "";
        
        if ($conditions instanceof Condition) {
            $whereClause = (string)$conditions;
            
            // Auto-detect joins from condition
            foreach (static::$foreignKeys as $model => $fkField) {
                $joinTable = call_user_func([$model, 'tableName']);
                if (strpos($whereClause, $joinTable) !== false) {
                    $joins[] = $model;
                }
            }
        } else {
            $conditionsArr = [];
            foreach ($kwargs as $k => $v) {
                $val = is_string($v) ? "'{$v}'" : $v;
                $conditionsArr[] = "{$tableName}.{$k} = {$val}";
            }
            $whereClause = implode(" AND ", $conditionsArr);
        }
        
        $sql = "SELECT {$tableName}.* FROM {$tableName}";
        
        // Add JOINs
        foreach ($joins as $joinModel) {
            $joinTable = call_user_func([$joinModel, 'tableName']);
            $fkField = static::$foreignKeys[$joinModel];
            $sql .= " JOIN {$joinTable} ON {$tableName}.{$fkField} = {$joinTable}.id";
        }
        
        if ($whereClause) {
            $sql .= " WHERE {$whereClause}";
        }
        
        $conn = static::connection();
        $stmt = $conn->query($sql);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        $objects = [];
        foreach ($rows as $row) {
            $objects[] = new static($row);
        }
        return $objects;
    }
    
    public static function update(array $where = [], array $data = []) {
        if (empty($data)) {
            throw new \Exception("No fields to update");
        }
        
        $tableName = static::tableName();
        $setClause = [];
        $setValues = [];
        
        foreach ($data as $k => $v) {
            $setClause[] = "{$k} = ?";
            $setValues[] = $v;
        }
        
        $whereClause = "";
        $whereValues = [];
        if (!empty($where)) {
            $whereParts = [];
            foreach ($where as $k => $v) {
                $whereParts[] = "{$k} = ?";
                $whereValues[] = $v;
            }
            $whereClause = " WHERE " . implode(" AND ", $whereParts);
        }
        
        $sql = "UPDATE {$tableName} SET " . implode(", ", $setClause) . $whereClause;
        
        $conn = static::connection();
        $stmt = $conn->prepare($sql);
        $stmt->execute(array_merge($setValues, $whereValues));
    }
    
    public function save() {
        $fields = static::fields();
        $names = array_keys($fields);
        $values = [];
        
        foreach ($names as $name) {
            $values[] = $this->$name ?? null;
        }
        
        $placeholders = implode(", ", array_fill(0, count($names), "?"));
        $tableName = static::tableName();
        $sql = "INSERT INTO {$tableName} (" . implode(", ", $names) . ") VALUES ({$placeholders})";
        
        $conn = static::connection();
        $stmt = $conn->prepare($sql);
        $stmt->execute($values);
        
        $pk = static::primaryKey();
        if ($pk) {
            $this->$pk = $conn->lastInsertId();
        }
    }
    
    public static function query() {
        return new QueryChainer(static::class);
    }
    
    public static function createTable() {
        $fields = static::fields();
        $tableName = static::tableName();
        $columns = [];
        
        foreach ($fields as $name => $type) {
            if ($type instanceof PrimaryKey) {
                $columns[] = "{$name} {$type}";
            } elseif ($type instanceof ForeignKey) {
                static::$foreignKeys[$type->targetModel] = $name;
                $columns[] = "{$name} {$type}";
            } elseif (isset(TypeMap::$map[$type])) {
                $columns[] = "{$name} " . TypeMap::$map[$type];
            } else {
                $columns[] = "{$name} {$type}";
            }
        }
        
        $sql = "CREATE TABLE IF NOT EXISTS {$tableName} (" . implode(", ", $columns) . ")";
        
        $conn = static::connection();
        $conn->exec($sql);
    }
    
    public static function describe() {
        echo "Table: " . static::tableName() . "\n";
        foreach (static::fields() as $field => $type) {
            $typeName = is_object($type) ? get_class($type) : $type;
            echo " {$field}: {$typeName}\n";
        }
    }
}

// Query Chainer class
class QueryChainer {
    private $model;
    private $conditions = [];
    private $kwargs = [];
    private $selectedFields = [];
    private $orderBy = [];
    private $groupBy = [];
    private $limit = null;
    private $count = false;
    private $typeFiller = null;
    
    public function __construct($model) {
        $this->model = $model;
    }
    
    public function orderBy(...$fields) {
        $this->orderBy = $fields;
        return $this;
    }
    
    public function groupBy(...$fields) {
        $this->groupBy = $fields;
        return $this;
    }
    
    public function count() {
        $this->count = true;
        return $this;
    }
    
    public function limit($n) {
        $this->limit = $n;
        return $this;
    }
    
    public function select(...$fields) {
        $this->selectedFields = $fields;
        return $this;
    }
    
    public function filter($conditions = null, array $kwargs = []) {
        if ($conditions instanceof Condition) {
            $this->conditions[] = $conditions;
        }
        $this->kwargs = array_merge($this->kwargs, $kwargs);
        return $this;
    }
    
    public function fillType($model) {
        $this->typeFiller = $model;
        return $this;
    }
    
    private function buildWhereAndJoins() {
        $joins = [];
        $clauses = [];
        
        if (!empty($this->conditions)) {
            $combined = $this->conditions[0];
            for ($i = 1; $i < count($this->conditions); $i++) {
                $combined = $combined->andCondition($this->conditions[$i]);
            }
            
            $whereClause = (string)$combined;
            
            // Collect all foreign key models from the main model
            $foreignKeys = $this->model::$foreignKeys ?? [];
            // var_dump($this->model::$foreignKeys);

            // Also check selected fields for foreign models
            $referencedModels = [];
            foreach ($this->selectedFields as $field) {
                if ($field instanceof Field) {
                    $fieldModel = $field->getModel();
                    if ($fieldModel && $fieldModel !== $this->model) {
                        $referencedModels[$fieldModel] = true;
                    }
                }
            }
            
            // Auto-detect joins from WHERE clause - check ALL models
            foreach ($foreignKeys as $modelClass => $fkField) {
                $tableName = call_user_func([$modelClass, 'tableName']);
                if (strpos($whereClause, $tableName) !== false || isset($referencedModels[$modelClass])) {
                    $joins[$modelClass] = $fkField;
                }
            }
            
            $clauses[] = $whereClause;
        }
        
        foreach ($this->kwargs as $k => $v) {
            $val = is_string($v) ? "'{$v}'" : $v;
            $tableName = call_user_func([$this->model, 'tableName']);
            $clauses[] = "{$tableName}.{$k} = {$val}";
        }
        
        $finalWhere = !empty($clauses) ? implode(" AND ", $clauses) : "";
        return [$finalWhere, $joins];
    }
    
    public function toSql() {
        $tableName = call_user_func([$this->model, 'tableName']);
        
        if ($this->count) {
            if (!empty($this->groupBy)) {
                $groupFields = array_map(function($f) {
                    return $f->fullName();
                }, $this->groupBy);
                $fieldList = implode(", ", $groupFields) . ", COUNT(*)";
            } else {
                $fieldList = "COUNT(*)";
            }
        } elseif (!empty($this->selectedFields)) {
            $fieldNames = array_map(function($f) {
                return $f->fullName();
            }, $this->selectedFields);
            $fieldList = implode(", ", $fieldNames);
        } else {
            $fieldList = "{$tableName}.*";
        }
        
        list($whereClause, $joins) = $this->buildWhereAndJoins();
        $sql = "SELECT {$fieldList} FROM {$tableName}";
        
        // Add JOINs - now $joins is an associative array [Model => fk_field]
        foreach ($joins as $joinModel => $fkField) {
            $joinTable = call_user_func([$joinModel, 'tableName']);
            $sql .= " JOIN {$joinTable} ON {$tableName}.{$fkField} = {$joinTable}.id";
        }
        
        if ($whereClause) {
            $sql .= " WHERE {$whereClause}";
        }
        
        if (!empty($this->groupBy)) {
            $groupFields = array_map(function($f) {
                return $f->fullName();
            }, $this->groupBy);
            $sql .= " GROUP BY " . implode(", ", $groupFields);
        }
        
        if (!empty($this->orderBy)) {
            $orderFields = array_map(function($f) {
                return $f->fullName();
            }, $this->orderBy);
            $sql .= " ORDER BY " . implode(", ", $orderFields);
        }
        
        if ($this->limit !== null) {
            $sql .= " LIMIT {$this->limit}";
        }
        
        return $sql;
    }
    
    public function all($jsonEnable = false) {
        $sql = $this->toSql();
        $conn = call_user_func([$this->model, 'connection']);
        $stmt = $conn->query($sql);
        $rows = $stmt->fetchAll(PDO::FETCH_ASSOC);
        
        if ($jsonEnable) {
            return json_encode($rows, JSON_PRETTY_PRINT);
        }
        
        $objects = [];
        foreach ($rows as $row) {
            if ($this->typeFiller) {
                $objects[] = new $this->typeFiller($row);
            } else {
                $objects[] = new $this->model($row);
            }
        }
        return $objects;
    }
    
    public function first() {
        $results = $this->all();
        return !empty($results) ? $results[0] : null;
    }
}

// Example Models
class User extends BaseModel {
    public $id;
    public $name;
    public $email;
    public $age;
    public $country;
    
    public static function fields() {
        return [
            'id' => new PrimaryKey('int'),
            'name' => 'string',
            'email' => 'string',
            'age' => 'int',
            'country' => 'string'
        ];
    }
}

class Post extends BaseModel {
    public $id;
    public $title;
    public $content;
    public $user_id;
    public $views;
    
    public static function fields() {
        return [
            'id' => new PrimaryKey('int'),
            'title' => 'string',
            'content' => 'string',
            'user_id' => new ForeignKey(User::class),
            'views' => 'int'
        ];
    }
}

class Author extends BaseModel {
    public $id;
    public $name;
    public $bio;
    
    public static function fields() {
        return [
            'id' => new PrimaryKey('int'),
            'name' => 'string',
            'bio' => 'string'
        ];
    }
}

class Publisher extends BaseModel {
    public $id;
    public $name;
    public $address;
    
    public static function fields() {
        return [
            'id' => new PrimaryKey('int'),
            'name' => 'string',
            'address' => 'string'
        ];
    }
}

class Book extends BaseModel {
    public $id;
    public $title;
    public $author_id;
    public $publisher_id;
    public $pages;
    
    public static function fields() {
        return [
            'id' => new PrimaryKey('int'),
            'title' => 'string',
            'author_id' => new ForeignKey(Author::class),
            'publisher_id' => new ForeignKey(Publisher::class),
            'pages' => 'int'
        ];
    }
}

// ============= TEST SCRIPT =============
echo "=== Creating Tables ===\n";
User::createTable();
Post::createTable();
Author::createTable();
Publisher::createTable();
Book::createTable();


// $q = Book::query()
//     ->select(Book::id(), Publisher::name())->filter(Book::id()->eq(2)->andCondition(Publisher::name()->eq("Meow")))->toSql();

// echo $q . "\n";


$q = Book::query()->select(Book::id())->filter(Book::title()->like("%Me"));

echo $q->toSql() . "\n";

// var_dump(User::$foreignKeys);

?>